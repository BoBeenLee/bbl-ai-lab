#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import ts from "typescript";

const workerRoot = path.resolve(import.meta.dirname, "..");
const repoRoot = path.resolve(workerRoot, "..");
const flowsPath = path.join(workerRoot, "src", "flows.ts");

const flowsModule = await importTypescriptModule(flowsPath);
const { FLOWS, flattenFlows, routeCommand } = flowsModule;

const errors = [];
const flattened = flattenFlows(FLOWS);

checkRouting();
checkManifestShape();
checkAdapters();

if (errors.length > 0) {
  for (const error of errors) {
    console.error(`flow check failed: ${error}`);
  }
  process.exit(1);
}

console.log(`flow check passed (${flattened.length} dispatch flow${flattened.length === 1 ? "" : "s"})`);

function checkRouting() {
  const idea = routeCommand("/idea hello", FLOWS);
  expect(idea.kind === "matched" && idea.flow.eventType === "idea-submitted" && idea.body === "hello",
    "/idea hello should route to idea-submitted");

  const todo = routeCommand("/todo hello", FLOWS);
  expect(todo.kind === "matched" && todo.flow.eventType === "idea-submitted" && todo.body === "hello",
    "/todo hello should route to idea-submitted");

  const ideaMissingBody = routeCommand("/idea", FLOWS);
  expect(ideaMissingBody.kind === "missing_body", "/idea without body should return the usage hint path");

  const plain = routeCommand("hello", FLOWS);
  expect(plain.kind === "missing_prefix", "plain text should require a command prefix");

  const unknown = routeCommand("/unknown hello", FLOWS);
  expect(unknown.kind === "unknown_command" && unknown.command === "unknown",
    "/unknown hello should be an unknown command");

  const syntheticSubcommandFlows = [{
    commands: ["recruit"],
    usageHint: "예: /recruit collect remoteok",
    subcommands: [{
      name: "collect",
      eventType: "recruit-collect",
      usageHint: "예: /recruit collect remoteok",
      ackText: "채용 데이터 수집을 시작합니다.",
      workflow: ".github/workflows/recruit-collect.yml",
      script: "scripts/recruit-collect.sh",
      prompt: "scripts/prompts/recruit-collect.md",
      docs: "docs/recruit-collect.md",
    }],
  }];
  const recruit = routeCommand("/recruit collect remoteok", syntheticSubcommandFlows);
  expect(recruit.kind === "matched" && recruit.flow.eventType === "recruit-collect" && recruit.body === "remoteok",
    "/recruit collect ... should be representable as a subcommand flow");

  const recruitMissingSubcommand = routeCommand("/recruit", syntheticSubcommandFlows);
  expect(recruitMissingSubcommand.kind === "missing_body",
    "/recruit without a subcommand should return the top-level usage hint path");
}

function checkManifestShape() {
  const seenCommands = new Set();
  const seenEvents = new Set();

  for (const flow of FLOWS) {
    expect(Array.isArray(flow.commands) && flow.commands.length > 0, "each flow needs at least one command");
    for (const command of flow.commands ?? []) {
      const normalized = command.toLowerCase();
      expect(command === normalized, `command must be lowercase: ${command}`);
      expect(!seenCommands.has(normalized), `duplicate command: ${command}`);
      seenCommands.add(normalized);
    }
  }

  for (const flow of flattened) {
    expect(flow.eventType.length > 0, `flow ${label(flow)} needs an eventType`);
    expect(!seenEvents.has(flow.eventType), `duplicate eventType: ${flow.eventType}`);
    seenEvents.add(flow.eventType);
    if (!flow.legacyEventType) {
      const expected = flow.subcommand ? `${flow.command}-${flow.subcommand}` : path.basename(flow.workflow, ".yml");
      expect(flow.eventType === expected,
        `${label(flow)} eventType should be ${expected}; mark legacyEventType only for pre-registry exceptions`);
    } else {
      expect(flow.eventType === "idea-submitted",
        `${label(flow)} uses a legacy eventType, but only idea-submitted is allowed`);
    }
  }
}

function checkAdapters() {
  for (const flow of flattened) {
    for (const key of ["workflow", "script", "prompt", "docs"]) {
      const relPath = flow[key];
      expect(typeof relPath === "string" && relPath.length > 0, `${label(flow)} is missing ${key}`);
      if (!relPath) continue;
      const absPath = path.join(repoRoot, relPath);
      expect(fs.existsSync(absPath), `${label(flow)} ${key} does not exist: ${relPath}`);
    }

    const workflowPath = path.join(repoRoot, flow.workflow);
    if (fs.existsSync(workflowPath)) {
      const eventTypes = readRepositoryDispatchTypes(workflowPath);
      expect(eventTypes.includes(flow.eventType),
        `${flow.workflow} repository_dispatch.types must include ${flow.eventType}`);
    }
  }
}

function readRepositoryDispatchTypes(workflowPath) {
  const text = fs.readFileSync(workflowPath, "utf8");
  const match = text.match(/repository_dispatch:[\s\S]*?types:\s*\[([^\]]+)\]/);
  if (!match) return [];
  return match[1]
    .split(",")
    .map((item) => item.trim().replace(/^['"]|['"]$/g, ""))
    .filter(Boolean);
}

function expect(condition, message) {
  if (!condition) errors.push(message);
}

function label(flow) {
  return flow.subcommand ? `/${flow.command} ${flow.subcommand}` : `/${flow.command}`;
}

async function importTypescriptModule(filePath) {
  const source = fs.readFileSync(filePath, "utf8");
  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
      moduleResolution: ts.ModuleResolutionKind.Bundler,
    },
    fileName: filePath,
  });
  const outPath = path.join(os.tmpdir(), `bbl-flow-check-${Date.now()}-${Math.random().toString(16).slice(2)}.mjs`);
  fs.writeFileSync(outPath, transpiled.outputText, "utf8");
  try {
    return await import(pathToFileURL(outPath).href);
  } finally {
    fs.rmSync(outPath, { force: true });
  }
}

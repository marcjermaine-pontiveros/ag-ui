#!/usr/bin/env node
import { Command } from "commander";
import inquirer from "inquirer";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const program = new Command();

// Dark purple color
const PURPLE = "\x1b[35m";
const RESET = "\x1b[0m";

function displayBanner() {
  const banner = `
${PURPLE}   █████╗  ██████╗       ██╗   ██╗ ██╗
  ██╔══██╗██╔════╝       ██║   ██║ ██║
  ███████║██║  ███╗█████╗██║   ██║ ██║
  ██╔══██║██║   ██║╚════╝██║   ██║ ██║
  ██║  ██║╚██████╔╝      ╚██████╔╝ ██║
  ╚═╝  ╚═╝ ╚═════╝        ╚═════╝  ╚═╝
${RESET}
  Agent User Interactivity Protocol
`;
  console.log(banner);
}

async function createProject() {
  displayBanner();

  console.log("\n~ Let's get started building an AG-UI powered user interactive agent ~");
  console.log("  Read more about AG-UI at https://ag-ui.com\n");
  console.log("");
  console.log("To build an AG-UI app, you need to select a client.");
  console.log("");

  const answers = await inquirer.prompt([
    {
      type: "list",
      name: "client",
      message: "What client do you want to use?",
      choices: [
        "CopilotKit/Next.js",
        new inquirer.Separator("Other clients coming soon (SMS, Whatsapp, Slack ...)"),
      ],
    },
  ]);

  console.log(`\nSelected client: ${answers.client}`);
  console.log("Initializing your project...\n");

  const packageJsonPath = path.join(process.cwd(), "package.json");
  const packageJsonExists = fs.existsSync(packageJsonPath);

  let projectDir = process.cwd();

  if (!packageJsonExists) {
    console.log("📦 No package.json found, creating a new Next.js app...\n");

    const projectName = await inquirer.prompt([
      {
        type: "input",
        name: "name",
        message: "What would you like to name your project?",
        default: "my-ag-ui-app",
        validate: (input) => {
          if (!input.trim()) {
            return "Project name cannot be empty";
          }
          if (!/^[a-zA-Z0-9-_]+$/.test(input)) {
            return "Project name can only contain letters, numbers, hyphens, and underscores";
          }
          return true;
        },
      },
    ]);

    projectDir = path.join(process.cwd(), projectName.name);

    console.log(`Creating Next.js app: ${projectName.name}\n`);

    const createNextApp = spawn(
      "npx",
      [
        "create-next-app@latest",
        projectName.name,
        "--typescript",
        "--tailwind",
        "--eslint",
        "--app",
        "--src-dir",
        "--import-alias",
        "@/*",
        "--no-turbopack",
      ],
      {
        stdio: "inherit",
        shell: true,
      },
    );

    await new Promise<void>((resolve, reject) => {
      createNextApp.on("close", (code) => {
        if (code === 0) {
          console.log("\n✅ Next.js app created successfully!");
          resolve();
        } else {
          console.log("\n❌ Failed to create Next.js app");
          reject(new Error(`create-next-app exited with code ${code}`));
        }
      });
    });

    // Change to the new project directory
    try {
      process.chdir(projectDir);
    } catch (error) {
      console.log("❌ Error changing directory:", error);
      process.exit(1);
    }
  }

  // Run copilotkit init with framework flags
  console.log("\n🚀 Running CopilotKit initialization...\n");
  
  const options = program.opts();
  const frameworkArgs = [];

  if (options.langgraph) {
    frameworkArgs.push("-m", "LangGraph");
  } else if (options.crewiAiCrews) {
    frameworkArgs.push("-m", "CrewAI", "--crew-type", "Crews");
  } else if (options.crewiAiFlows) {
    frameworkArgs.push("-m", "CrewAI", "--crew-type", "Flows");
  } else if (options.mastra) {
    frameworkArgs.push("-m", "Mastra");
  } else if (options.ag2) {
    frameworkArgs.push("-m", "AG2");
  } else if (options.llamaindex) {
    frameworkArgs.push("-m", "LlamaIndex");
  } else if (options.agno) {
    frameworkArgs.push("-m", "Agno");
  }

  const copilotkit = spawn("npx", ["copilotkit", "init", ...frameworkArgs], {
    stdio: "inherit",
    shell: true,
  });

  copilotkit.on("close", (code) => {
    if (code !== 0) {
      console.log("\n❌ Project creation failed.");
    }
  });
}

program.name("create-ag-ui-app").description("AG-UI CLI").version("0.0.1-alpha.1");

// Add framework flags
program
  .option("--langgraph", "Use the LangGraph framework")
  .option("--crewi-ai-crews", "Use the CrewAI framework with Crews")
  .option("--crewi-ai-flows", "Use the CrewAI framework with Flows")
  .option("--mastra", "Use the Mastra framework")
  .option("--ag2", "Use the AG2 framework")
  .option("--llamaindex", "Use the LlamaIndex framework")
  .option("--agno", "Use the Agno framework");


program.action(async () => {
  await createProject();
});

program.parse();

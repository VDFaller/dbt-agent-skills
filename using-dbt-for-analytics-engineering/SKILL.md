---
name: using-dbt-for-analytics-engineering
description: The core workflow loop when asked to interact with a dbt project. Includes best practices on developing and configuring models, adding tests, and refactoring projects. Use whenever working with dbt.
---

# Using dbt for analytics engineering

Analytics engineering moves data work away from one-off, ad-hoc queries and towards a software engineering mindset of reusability, composability and modularity. dbt is the best way to implement this mindset.

The user provides requirements: a model, test, group of sources, or entire project to build. They may include context about the purpose, audience, or technical constraints.

## DAG building guidelines

- Conform to the existing style of a project (medallion layers, stage/intermediate/mart, etc)
- Focus heavily on DRY principles.
  - Before adding a new model or column, always be sure that the same logic isn't already defined elsewhere that can be used.
  - Prefer a change that requires you to add one column to an existing intermediate model over adding an entire additional model to the project.

## Model building guidelines

- Always use data modelling best practices when working in a project
- Write dbtonic code:
  - Always use `{{ ref }}` and `{{ source }}` over hardcoded table names
  - Use CTEs over subqueries
- Before beginning to build a model, you should plan it using the [planning-dbt-models](/dbt-commands/planning-dbt-models/SKILL.md) skill.
- When implementing a model, you should use `dbt show` regularly to:
  - preview the input data you will work with, so that you use relevant columns and values
  - preview the results of your model, so that you know your work is correct
  - run basic data profiling (counts, min, max, nulls) of input and output data, to check for misconfigured joins or other logic errors

## Interacting with the CLI

- You will be working in a terminal environment where you have access to the dbt CLI, and potentially the dbt MCP server. The MCP server may include access to the dbt Cloud platform's APIs if relevant.
- You should prefer working with the dbt MCP server's tools, and help the user install and onboard the MCP when appropriate.
- You should not circumvent the dbt abstraction layer to execute DDL directly against the warehouse.

## Common misconceptions

Working with data is different than working with code. LLMs are often good at changing multiple things in a codebase simultaneously. You should not assume that you know how to one-shot a task - use the [planning skill](/dbt-commands/planning-dbt-models/SKILL.md). You should not assume you know the schema of tables - use the [discovering-data skill](/dbt-commands/discovering-data/SKILL.md).

Ensure that you are not unnecessarily creating resources in the database. Code may be cheap, but the underlying data platforms have costs associated with them. You must consider the cost of adding additional models.

dbt has a low barrier to entry, but is highly configurable and configuration can be applied in many places or cascade throughout a project. When changing configurations, do so surgically and taking into account the existing patterns in the project.

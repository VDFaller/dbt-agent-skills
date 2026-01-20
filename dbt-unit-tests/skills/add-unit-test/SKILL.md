---
name: adding-dbt-unit-test
description: Use when adding unit tests for a dbt model
---

# Add unit test for a dbt model

## Overview

Unit tests allow enforcing that all the unit tests for a model pass before it is materialized (i.e. dbt won't materialize the model in the database if *any* of its unit tests do not pass).

## When to use

- Adding Model-Input-Output scenarios for the general case and edge cases
- Verifying that a bug fix solves a bug report for an existing dbt model

### TODO - split these into separate skill(s)
- Using Test-Driven Development (TDD) for a dbt model that hasn't been added to a dbt project yet
- Preventing regressions when refactoring an existing dbt model

## General format

The general format of a dbt unit test looks like this:
1. `given` - given a set of source, seeds, and models as preconditions
2. `model` - when building this model
3. `expect` - then expect this row content of the model as a postcondition

There are similar concepts this lines up with (Hoare triple, Arrange-Act-Assert, Gherkin, What's in a Story?, etc):

TODO: take out the links(?)! Replace with explicit insights that we want it to know about.

| dbt unit test | Description                                | [Hoare triple](https://en.wikipedia.org/wiki/Hoare_logic#Hoare_triple) | [Arrange-Act-Assert](https://docs.pytest.org/en/7.1.x/explanation/anatomy.html) | [Gherkin](https://cucumber.io/docs/gherkin/reference/) | [What's in a Story?](https://dannorth.net/whats-in-a-story/#the-scenario-should-be-described-in-terms-of-givens-events-and-outcomes) |
|---------------|--------------------------------------------|------------------------------------------------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| **`given`**   | given these test inputs as  preconditions  | Precondition                                                           | Arrange                                                                         | Given                                                  | Givens                                                                                                                               |
| **`model`**   | when running the command for this model    | Command                                                                | Act                                                                             | When                                                   | Event                                                                                                                                |
| **`expect`**  | then expect this output as a postcondition | Postcondition                                                          | Assert                                                                          | Then                                                   | Outcome                                                                                                                              |

### Workflow

### 1. Choose the model to test
Self explanatory -- the title says it all!

### 2. Mock the inputs
Create an input for each of the nodes the model depends on and specify the data it should use a mock.

### 3. Mock the output
Specify the data that you expect the model to create given those inputs.

## Minimal unit test

Suppose you have this model:

```sql
-- models/hello_world.sql

select 'world' as hello
```

Minimal unit test for that model:

```yaml
# models/_properties.yml

unit_tests:
  - name: test_hello_world

    # Always only one transformation to test
    model: hello_world

    # No inputs needed this time!
    # Most unit tests will have inputs -- see the "real world example" section below
    given: []

    # Expected output can have zero to many rows
    expect:
      rows:
        - {hello: world}
```

Run the unit tests and then build the model:

```shell
dbt build --select hello_world
```

Or only run the unit tests without building the model:

```shell
dbt test --select hello_world 
```

## Real world example

```yaml
unit_tests:

  - name: test_order_items_count_drink_items_with_zero_drinks
    description: >
      Scenario: Order without any drinks
        When the `order_items_summary` table is built
        Given an order with nothing but 1 food item
        Then the count of drink items is 0

    # Model
    model: order_items_summary

    # Inputs
    given:
      - input: ref('order_items')
        rows:
          - {
              order_id: 76,
              order_item_id: 3,
              is_drink_item: false,
            }
      - input: ref('stg_orders')
        rows:
          - { order_id: 76 }

    # Output
    expect:
      rows:
        - {
            order_id: 76,
            count_drink_items: 0,
          }
```

### YAML format

### SQL format

### Adapter-specific caveats

#### Examples for different data types

### Columns to include / ignore

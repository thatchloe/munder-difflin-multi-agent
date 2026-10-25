# Munder Difflin Multi-Agent System – Design Notes & Reflection

Files in this submission:

| File | Purpose |
|---|---|
| `project_starter.py` | Complete implementation (starter helpers + agents + evaluation loop) |
| `agent_workflow_figma.png` | Agent workflow diagram exported from FigJam ([editable board](https://www.figma.com/board/9B9TxcwmQUb16RDunMmJ08)) |
| `agent_workflow_diagram.png` / `.mmd` | Same workflow as Mermaid source and rendered image |
| `test_results.csv` | Output of `run_test_scenarios()` on `quote_requests_sample.csv` |
| `design_notes.md` | This report |

Run it with `pip install -r requirements.txt`, put `UDACITY_OPENAI_API_KEY=...` in `.env`, then `python project_starter.py`.

---

## 1. Framework choice: Pydantic AI

I chose **pydantic-ai** (v2.61, model `gpt-4.1-mini` through the Vocareum OpenAI-compatible proxy) because:

- **Typed tools.** Tool arguments are validated against Python type hints and Pydantic models (e.g. `List[StockRequest]`), so malformed LLM calls are rejected and retried automatically.
- **Agent delegation.** An orchestrator tool can `await worker_agent.run(..., usage=ctx.usage)`. This is exactly the orchestrator → worker pattern, and token usage is tracked across all agents.
- **Shared dependencies.** A per-request `RequestContext` dataclass is passed as `deps` to every agent. Hard facts (request date, deadline, secured quantities, the computed quote) move between agents as data, not as text the LLM could rewrite.

## 2. Starter helper functions (Step 2 review)

| Helper | What it does | Where it is used |
|---|---|---|
| `generate_sample_inventory` | Seeds a reproducible inventory covering 40% of the 50-item catalog, with stock 200–800 and a min level of 50–150 | Called by `init_database` |
| `init_database` | Builds the `transactions`, `quote_requests`, `quotes` and `inventory` tables and seeds $50k cash plus the opening stock purchases | `run_test_scenarios` (the stub called it without `db_engine`; fixed) |
| `create_transaction` | Inserts a `stock_orders` or `sales` row | Inventory agent (supplier reorders), Fulfillment agent (sales) |
| `get_all_inventory` | Net stock of every item with positive stock as of a date | Inventory agent `get_inventory_snapshot` |
| `get_stock_level` | Net stock of one item as of a date | Inventory agent `check_and_secure_stock`, Fulfillment agent `fulfill_quoted_order` |
| `get_supplier_delivery_date` | Supplier lead time by quantity (same day / 1 / 4 / 7 days) | Inventory agent: decides whether a restock can arrive before the customer's deadline |
| `get_cash_balance` | Sales minus stock purchases as of a date | Inventory agent (cash guard before reorders), Fulfillment agent `check_cash_balance` |
| `generate_financial_report` | Cash, inventory value, total assets, itemised stock, top sellers | Fulfillment agent `financial_health_check` (mandatory for quotes above $500), plus the evaluation loop |
| `search_quote_history` | Keyword search over historical quotes and requests | Quoting agent `search_past_quotes` |

## 3. Architecture (4 agents; the limit is 5)

See `agent_workflow_diagram.png`. Each customer request flows **Orchestrator → Inventory → Quoting → Fulfillment → Orchestrator reply**.

1. **Orchestrator agent.** Reads the request and extracts the delivery deadline, then calls three delegation tools in order: `assess_inventory`, `prepare_quote` (only if something could be supplied) and `finalize_order` (only if a quote exists). It writes the customer reply: delivered items and dates, the total charged, and a clear reason for every rejected item. It is told never to reveal costs, markups, cash or stock counts.
2. **Inventory agent.** The LLM's only judgement call is mapping customer wording to exact catalog names (e.g. "A4 glossy" → `Glossy paper`, "poster board" → `Large poster paper (24x36 inches)`, "balloons" → no match). It then calls `check_and_secure_stock` **once** with every request line. That tool applies the restock policy deterministically:
   - item not sold, or not stocked → *unavailable*
   - enough stock → *available*; if the sale would leave stock below `min_stock_level`, a replenishment order is placed
   - short of stock → reorder the shortfall plus the min level, but only if the supplier can deliver by the deadline and cash stays above a $2,000 reserve; otherwise *unavailable* with the supplier date as the reason
3. **Quoting agent.** Looks up similar past quotes, then calls `calculate_quote`. That tool prices exactly the secured items:
   - list price = catalog cost × 1.20
   - bulk discount on total units: 5% at ≥500, 10% at ≥1,000, 15% at ≥5,000
   - the gross margin never drops below 2%

   The agent writes the customer-facing explanation and mentions the next discount tier to encourage larger orders.
4. **Fulfillment agent.** Checks the cash balance and runs `financial_health_check` (`generate_financial_report`) before large orders. `fulfill_quoted_order` then re-checks each line's stock and ship date against the deadline before writing a `sales` transaction.

**Design principle:** LLMs handle language (matching item names, explanations, customer emails). Python tools own every number, policy decision and database write. Early test runs showed why. With LLM-driven reorder decisions, `gpt-4o-mini` skipped needed reorders, probed with quantity 1, and looped on repeated reorders until it hit the request limit. Moving those decisions into tools, making the stock check a single batched call, and passing tool results (not LLM summaries) back to the orchestrator removed all of these failures.

## 4. Evaluation results (`test_results.csv`)

20 sample requests were processed with no runtime errors.

| Outcome | Requests | Count |
|---|---|---|
| Fully fulfilled | 1, 4, 10 | 3 |
| Partially fulfilled (some items declined with reasons) | 2, 3, 5, 6, 7, 8, 9, 11, 12, 14, 16, 17, 19, 20 | 14 |
| Fully declined with reasons | 13 (supplier can't beat the Apr 10 deadline), 15 (supplier restock arrives Apr 19 > Apr 15; cardboard not sold), 18 (all restocks arrive after Apr 15) | 3 |

Financials (2025-03-31 → 2025-04-17):

| | Start | End |
|---|---|---|
| Cash | $45,059.70 | $46,571.85 |
| Inventory value | $4,940.30 | $4,053.90 |
| Total assets | $50,000.00 | **$50,625.75** (+$625.75) |

27 sale transactions brought in $17,393.25 against $15,881.10 of supplier restocks. Cash changes on 17 requests, matching the number of requests where something was sold.

**Strengths**

- **Impossible constraints are recognised.** Lead-time rules are enforced exactly. Request 14 explains that 5,000 A4 sheets would take 7 days (arriving Apr 16) against an Apr 15 deadline. Request 9 offers Apr 11 as an alternative date.
- **Reordering serves sales and future demand.** Shortfalls are restocked when the supplier can still make the deadline (e.g. request 20: 1,790 poster sheets ordered to fill a 2,000 order due May 15). Items that drop below their minimum level are replenished.
- **Pricing is transparent and consistent.** Every reply's totals match the `sales` rows exactly, because the price comes from one deterministic calculation shared by the quoting and fulfillment agents.
- **Replies are safe to send.** No internal costs, cash figures, stock counts or placeholder signatures appear.

**Weaknesses / areas for improvement observed**

- **Item matching is still a judgement call.** "Colorful poster paper" was matched to `Colored paper` (request 2) rather than poster paper, and two lines in request 3 were merged into 260,000 A4 sheets. "500 reams of printer paper" was correctly read as 250,000 sheets, but nobody confirmed a ~$13k order with the customer.
- **Many requests fail because only 18 of 50 catalog items are stocked.** The policy never sources unstocked catalog items, which costs sales (washi tape, napkins, recycled paper, matte paper).
- **The ledger shows stock earlier than it arrives.** Sales and restocks are dated on the request date, while the customer delivery date reflects supplier lead time. Stock is effectively reserved before it physically arrives.

## 5. Suggestions for further improvement

1. **Add a customer-confirmation step for large or ambiguous orders.** When the quote exceeds a threshold (e.g. $2,000) or an item match has low confidence, return a quote and wait for approval instead of booking the sale immediately. This would have caught the request 3 interpretation. It could also offer substitutes ("we don't stock matte paper; glossy is available").
2. **Source unstocked catalog items on demand.** Let the inventory agent order catalog items that aren't in the warehouse when the supplier can meet the deadline. This would recover sales that are currently lost to "not stocked". Add those items to the `inventory` table so `generate_financial_report` values them.
3. **Model inbound deliveries properly.** Date `stock_orders` on the supplier arrival date and track reserved vs. available stock. Same-day requests would then not compete for stock that hasn't arrived yet, and the reports would reflect real on-hand inventory.
4. **Price dynamically from history and margin.** Use `search_quote_history` totals to calibrate discounts per job type and event type, and add a margin floor that accounts for restock cost, rather than fixed tiers.
5. **Add structured matching evaluation.** Keep a labelled set of request lines with their correct catalog item and score the inventory agent's mapping in CI. The model is the main remaining source of error.

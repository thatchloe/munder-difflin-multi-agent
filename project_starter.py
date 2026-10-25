import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# Set up and load your env parameters and instantiate your model.
import re
from dataclasses import dataclass, field
from typing import Optional

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

dotenv.load_dotenv()

model = OpenAIChatModel(
    "gpt-4.1-mini",
    provider=OpenAIProvider(
        base_url="https://openai.vocareum.com/v1",
        api_key=os.getenv("UDACITY_OPENAI_API_KEY"),
    ),
)

# Business rules
# Catalog unit_price is the supplier cost basis (it is what init_database pays for stock),
# so customers are quoted a list price with a markup and then receive bulk discounts.
LIST_PRICE_MARKUP = 1.20
BULK_DISCOUNT_TIERS = [(5000, 0.15), (1000, 0.10), (500, 0.05)]  # (min total units, discount)
MIN_CASH_RESERVE = 2000.0           # restock purchases may not push cash below this
LARGE_ORDER_THRESHOLD = 500.0       # quotes above this trigger a financial health check

CATALOG = {item["item_name"]: item for item in paper_supplies}


@dataclass
class RequestContext:
    """Per-request state shared by all agents through Pydantic AI dependencies."""
    request_date: str
    deadline: Optional[str] = None
    quote: Optional[Dict] = None
    secured: Dict[str, int] = field(default_factory=dict)      # item -> quantity we can supply
    stock_results: Optional[List[Dict]] = None                 # output of the single stock check
    ready_dates: Dict[str, str] = field(default_factory=dict)  # item -> date stock is on hand


def _normalize_date(value: str) -> str:
    """Return a YYYY-MM-DD string (raises ValueError on bad input)."""
    return datetime.fromisoformat(str(value).split("T")[0]).strftime("%Y-%m-%d")


def _carried_items() -> Dict[str, Dict]:
    """Items the company actively stocks, keyed by name, with their min_stock_level."""
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    return {row["item_name"]: row for row in inventory_df.to_dict(orient="records")}


def _resolve_item(item_name: str) -> Optional[str]:
    """Return the exact catalog name for a case-insensitive match, or None."""
    lookup = {name.lower(): name for name in CATALOG}
    return lookup.get(item_name.strip().lower())


def _current_stock(item_name: str, as_of_date: str) -> int:
    return int(get_stock_level(item_name, as_of_date)["current_stock"].iloc[0])


def _bulk_discount(total_units: int) -> float:
    for min_units, rate in BULK_DISCOUNT_TIERS:
        if total_units >= min_units:
            return rate
    return 0.0


"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""


# Output schemas exchanged between agents

class QuoteSummary(BaseModel):
    total_amount: float
    discount_rate: float
    explanation: str = Field(description="Customer-facing explanation of the pricing")


class FulfillmentResult(BaseModel):
    fulfilled_items: List[str]
    unfulfilled_items: List[str]
    total_charged: float
    delivery_date: Optional[str]
    summary: str


# Worker agents

inventory_agent = Agent(
    model,
    deps_type=RequestContext,
    output_type=str,
    name="inventory_agent",
    instructions=(
        "You are the inventory manager for Munder Difflin Paper Company.\n"
        "1. Call list_catalog once. Map each requested item to the single closest catalog item_name using these "
        "rules: catalog paper types are not size-specific, so ignore sheet sizes like A3/A4/A5 when a paper type "
        "is given ('A3 glossy paper' -> 'Glossy paper', 'A4 matte paper' -> 'Matte paper', 'A4 recycled paper' -> "
        "'Recycled paper', 'colored construction paper' -> 'Construction paper', 'heavy/white cardstock' -> "
        "'Cardstock', 'poster board' or 'posters' -> 'Large poster paper (24x36 inches)', 'washi tape' -> "
        "'Decorative adhesive tape (washi tape)', 'table napkins' -> 'Paper napkins', 'streamers' -> 'Party "
        "streamers'). Plain white/printer/printing/copy paper in A4 or unspecified size -> 'A4 paper'. Plain "
        "paper in another size with no paper type (e.g. 'A3 paper') has no match. Items unrelated to the catalog "
        "(balloons, tickets, cardboard) have no match.\n"
        "2. Use the exact quantity the customer states for each item (sheets, rolls, units, packets). The only "
        "conversion is reams: 1 ream = 500 sheets.\n"
        "3. Call check_and_secure_stock exactly ONCE with one entry per requested line: the customer's wording, "
        "the matched catalog item_name (null when there is no match) and the quantity. It applies the "
        "restocking policy and places supplier reorders itself.\n"
        "4. Reply with a one or two sentence summary of the outcome."
    ),
)


@inventory_agent.tool_plain
def list_catalog() -> List[Dict]:
    """List every product Munder Difflin sells and whether the warehouse currently carries it."""
    carried = _carried_items()
    return [
        {"item_name": name, "category": item["category"], "carried_in_warehouse": name in carried}
        for name, item in CATALOG.items()
    ]


@inventory_agent.tool_plain
def get_inventory_snapshot(as_of_date: str) -> Dict[str, int]:
    """Return all items with positive stock as of a YYYY-MM-DD date."""
    return {k: int(v) for k, v in get_all_inventory(_normalize_date(as_of_date)).items()}


def _place_stock_order(deps: RequestContext, item_name: str, quantity: int, unit_price: float) -> Dict:
    """Record a supplier purchase if cash stays above the reserve. Returns the outcome."""
    cost = round(quantity * unit_price, 2)
    cash = get_cash_balance(deps.request_date)
    if quantity <= 0 or cash - cost < MIN_CASH_RESERVE:
        return {"success": False, "cost": cost}
    arrival = get_supplier_delivery_date(deps.request_date, quantity)
    transaction_id = create_transaction(item_name, "stock_orders", quantity, cost, deps.request_date)
    return {"success": True, "transaction_id": transaction_id, "units": quantity,
            "cost": cost, "supplier_arrival_date": arrival}


class StockRequest(BaseModel):
    requested_item: str = Field(description="The line item in the customer's own words")
    item_name: Optional[str] = Field(description="Exact catalog item name, or null if nothing matches")
    quantity: int = Field(description="Quantity the customer asked for, in units/sheets")


def _secure_item(deps: RequestContext, name: str, quantity: int) -> Dict:
    """Apply the restocking policy to one catalog item and record what can be supplied."""
    carried = _carried_items()
    if name not in carried:
        return {"item_name": name, "status": "unavailable",
                "reason": "This item is in our catalog but is not currently stocked by our warehouse."}

    unit_price = float(carried[name]["unit_price"])
    min_level = int(carried[name]["min_stock_level"])
    stock = _current_stock(name, deps.request_date)

    if stock >= quantity:
        remaining = stock - quantity
        reorder = None
        if remaining < min_level:
            reorder = _place_stock_order(deps, name, min_level * 2 - remaining, unit_price)
        deps.secured[name] = quantity
        deps.ready_dates[name] = deps.request_date
        return {"item_name": name, "quantity": quantity, "status": "available", "ready_date": deps.request_date,
                "reason": "In stock.", "replenishment_order": reorder}

    reorder_qty = quantity - stock + min_level
    arrival = get_supplier_delivery_date(deps.request_date, reorder_qty)
    if deps.deadline and arrival > deps.deadline:
        return {"item_name": name, "quantity": quantity, "status": "unavailable",
                "reason": f"Not enough stock on hand, and our supplier's earliest delivery ({arrival}) "
                          f"is after the requested deadline ({deps.deadline})."}

    reorder = _place_stock_order(deps, name, reorder_qty, unit_price)
    if not reorder["success"]:
        return {"item_name": name, "quantity": quantity, "status": "unavailable",
                "reason": "We cannot finance a restock of this size right now."}
    deps.secured[name] = quantity
    deps.ready_dates[name] = arrival
    return {"item_name": name, "quantity": quantity, "status": "restocked", "ready_date": arrival,
            "reason": f"Restocked from our supplier; ready to ship by {arrival}.", "restock_order": reorder}


@inventory_agent.tool
def check_and_secure_stock(ctx: RunContext[RequestContext], items: List[StockRequest]) -> Dict:
    """Check and secure stock for ALL matched items of the request in a single call.

    Restocking policy: if stock is short, reorder the shortfall plus the item's minimum stock level, but only
    when the supplier can deliver by the deadline and cash allows. If the sale would leave stock below the
    minimum level, place a replenishment order so future customers are covered.
    """
    deps = ctx.deps
    if deps.stock_results is not None:
        return {"note": "Stock was already secured for this request; reuse these results.",
                "results": deps.stock_results}

    # Lines that map to the same catalog item (e.g. 'A4 paper' and 'printer paper') are combined.
    totals: Dict[str, int] = {}
    for line in items:
        name = _resolve_item(line.item_name or "")
        if name is not None and line.quantity > 0:
            totals[name] = totals.get(name, 0) + line.quantity
    by_item = {name: _secure_item(deps, name, qty) for name, qty in totals.items()}

    results = []
    for line in items:
        name = _resolve_item(line.item_name or "")
        outcome = by_item.get(name) or {"status": "unavailable", "reason": "We do not sell this item."}
        results.append({"requested_item": line.requested_item, "quantity": line.quantity,
                        "our_product": name, **{k: v for k, v in outcome.items() if k in ("status", "ready_date", "reason")}})
    deps.stock_results = results
    return {"results": results}


quoting_agent = Agent(
    model,
    deps_type=RequestContext,
    output_type=QuoteSummary,
    name="quoting_agent",
    instructions=(
        "You are the sales quoting specialist for Munder Difflin Paper Company.\n"
        "1. Call search_past_quotes with one or two short keywords (e.g. an event type or main paper type) "
        "to see how similar orders were priced and explained.\n"
        "2. Call calculate_quote exactly once; it prices every item inventory secured. Its numbers are final.\n"
        "3. Write a warm, concise customer-facing explanation listing each item, quantity and line total, "
        "the bulk discount applied, and the total. Encourage larger orders by mentioning the next discount tier "
        "when relevant. Do not mention internal costs, markups, margins or cash balances."
    ),
)


@quoting_agent.tool_plain
def search_past_quotes(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """Search historical quotes. All terms must match, so use only one or two keywords."""
    return search_quote_history(search_terms, limit=limit)


@quoting_agent.tool
def calculate_quote(ctx: RunContext[RequestContext]) -> Dict:
    """Price the items inventory secured using list prices and the bulk discount tier for the total quantity."""
    secured = ctx.deps.secured
    total_units = sum(secured.values())
    discount = _bulk_discount(total_units)

    lines = []
    for name, qty in secured.items():
        unit_price = round(CATALOG[name]["unit_price"] * LIST_PRICE_MARKUP * (1 - discount), 4)
        lines.append({"item_name": name, "quantity": qty,
                      "unit_price": unit_price, "line_total": round(unit_price * qty, 2)})

    subtotal = round(sum(CATALOG[name]["unit_price"] * LIST_PRICE_MARKUP * qty for name, qty in secured.items()), 2)
    total = round(sum(line["line_total"] for line in lines), 2)
    next_tier = next(((units, rate) for units, rate in reversed(BULK_DISCOUNT_TIERS) if units > total_units), None)

    quote = {"lines": lines, "total_units": total_units, "subtotal_before_discount": subtotal,
             "discount_rate": discount, "total_amount": total,
             "next_discount_tier": {"min_units": next_tier[0], "discount": next_tier[1]} if next_tier else None}
    ctx.deps.quote = quote
    return quote


fulfillment_agent = Agent(
    model,
    deps_type=RequestContext,
    output_type=FulfillmentResult,
    name="fulfillment_agent",
    instructions=(
        "You are the order fulfillment manager for Munder Difflin Paper Company.\n"
        "1. Call check_cash_balance for the request date.\n"
        "2. If the quote total is above the large-order threshold, call financial_health_check before fulfilling.\n"
        "3. Call fulfill_quoted_order exactly once to record the sale.\n"
        "4. Report which items were fulfilled or not (with reasons), the total charged and the delivery date. "
        "Do not invent numbers; only use tool outputs."
    ),
)


@fulfillment_agent.tool
def check_cash_balance(ctx: RunContext[RequestContext]) -> float:
    """Return the company's cash balance as of the request date."""
    return round(get_cash_balance(ctx.deps.request_date), 2)


@fulfillment_agent.tool
def financial_health_check(ctx: RunContext[RequestContext]) -> Dict:
    """Summarize cash, inventory value, total assets, low-stock items and top sellers as of the request date."""
    report = generate_financial_report(ctx.deps.request_date)
    carried = _carried_items()
    low_stock = [row["item_name"] for row in report["inventory_summary"]
                 if row["item_name"] in carried and row["stock"] < carried[row["item_name"]]["min_stock_level"]]
    return {"cash_balance": round(report["cash_balance"], 2),
            "inventory_value": round(report["inventory_value"], 2),
            "total_assets": round(report["total_assets"], 2),
            "low_stock_items": low_stock,
            "top_selling_products": report["top_selling_products"],
            "large_order_threshold": LARGE_ORDER_THRESHOLD}


@fulfillment_agent.tool
def fulfill_quoted_order(ctx: RunContext[RequestContext]) -> Dict:
    """Record sales transactions for every quoted line that is in stock and can ship by the deadline."""
    deps = ctx.deps
    if not deps.quote or not deps.quote["lines"]:
        return {"fulfilled": [], "unfulfilled": [], "total_charged": 0.0, "reason": "No quote to fulfill."}

    fulfilled, unfulfilled = [], []
    for line in deps.quote["lines"]:
        item, qty = line["item_name"], line["quantity"]
        ship_date = deps.ready_dates.get(item, deps.request_date)
        stock = _current_stock(item, deps.request_date)
        if stock < qty:
            unfulfilled.append({"item_name": item, "reason": f"Insufficient stock ({stock} on hand, {qty} needed)."})
        elif deps.deadline and ship_date > deps.deadline:
            unfulfilled.append({"item_name": item, "reason": f"Cannot ship before {ship_date}, after the deadline."})
        else:
            transaction_id = create_transaction(item, "sales", qty, line["line_total"], deps.request_date)
            fulfilled.append({**line, "transaction_id": transaction_id, "ship_date": ship_date})

    return {"fulfilled": fulfilled, "unfulfilled": unfulfilled,
            "total_charged": round(sum(line["line_total"] for line in fulfilled), 2),
            "delivery_date": max((line["ship_date"] for line in fulfilled), default=None),
            "cash_after_sale": round(get_cash_balance(deps.request_date), 2)}


# Set up your agents and create an orchestration agent that will manage them.

orchestrator_agent = Agent(
    model,
    deps_type=RequestContext,
    output_type=str,
    name="orchestrator_agent",
    instructions=(
        "You are the customer service orchestrator for Munder Difflin Paper Company. Every customer request "
        "is treated as an order. Follow these steps in order:\n"
        "1. Call assess_inventory with the customer's full, unedited request text and the delivery deadline "
        "(YYYY-MM-DD) stated by the customer.\n"
        "2. If at least one line is 'available' or 'restocked', call prepare_quote.\n"
        "3. If a quote was prepared, call finalize_order. Only items it reports as fulfilled are sold.\n"
        "4. Reply to the customer in a professional, friendly message: each item that will be delivered (using "
        "our product name) and the delivery date, the pricing explanation and total actually charged, and for "
        "every item that cannot be supplied a clear reason (we don't sell it, we don't currently stock it, or "
        "our supplier cannot deliver before their deadline) with an alternative or a later date where sensible. "
        "If nothing can be supplied, politely decline and explain why.\n"
        "Never reveal internal costs, markups, cash balances, stock counts or transaction ids. Do not use "
        "placeholders such as [Your Name]; sign off as 'Munder Difflin Sales Team'."
    ),
)


@orchestrator_agent.tool
async def assess_inventory(ctx: RunContext[RequestContext], request_text: str, deadline: str) -> Dict:
    """Ask the inventory agent to match requested items to the catalog, check stock and reorder if needed."""
    try:
        ctx.deps.deadline = _normalize_date(deadline)
    except ValueError:
        ctx.deps.deadline = None
    result = await inventory_agent.run(
        f"Request date: {ctx.deps.request_date}. Deadline: {ctx.deps.deadline}.\nCustomer request:\n{request_text}",
        deps=ctx.deps, usage=ctx.usage,
    )
    if ctx.deps.stock_results is None:
        return {"error": "Inventory check did not complete; call assess_inventory again."}
    # The orchestrator works from the tool's recorded results, not the agent's free-text summary.
    return {"lines": ctx.deps.stock_results, "inventory_notes": result.output}


@orchestrator_agent.tool
async def prepare_quote(ctx: RunContext[RequestContext], customer_context: str) -> Dict:
    """Ask the quoting agent to price the items inventory secured and write the pricing explanation.
    `customer_context` describes the customer and event (e.g. 'school teacher, assembly')."""
    item_list = "\n".join(f"- {qty} x {name}" for name, qty in ctx.deps.secured.items())
    result = await quoting_agent.run(
        f"Customer context: {customer_context}\nItems to quote:\n{item_list}",
        deps=ctx.deps, usage=ctx.usage,
    )
    return {**result.output.model_dump(), "lines": (ctx.deps.quote or {}).get("lines", [])}


@orchestrator_agent.tool
async def finalize_order(ctx: RunContext[RequestContext]) -> Dict:
    """Ask the fulfillment agent to run financial checks and record the sale for the prepared quote."""
    quote = ctx.deps.quote
    if not quote:
        return {"error": "No quote has been prepared yet."}
    is_large = quote["total_amount"] > LARGE_ORDER_THRESHOLD
    result = await fulfillment_agent.run(
        f"Request date: {ctx.deps.request_date}. Deadline: {ctx.deps.deadline}. "
        f"Quote total ${quote['total_amount']:.2f} is {'ABOVE' if is_large else 'below'} the "
        f"${LARGE_ORDER_THRESHOLD:.2f} large-order threshold.\nQuote: {quote}",
        deps=ctx.deps, usage=ctx.usage,
    )
    return result.output.model_dump()


def call_multi_agent_system(request_with_date: str) -> str:
    """Run one customer request through the orchestrator and return the customer-facing response."""
    match = re.search(r"Date of request: (\d{4}-\d{2}-\d{2})", request_with_date)
    request_date = match.group(1) if match else datetime.now().strftime("%Y-%m-%d")
    try:
        result = orchestrator_agent.run_sync(request_with_date, deps=RequestContext(request_date=request_date))
        return result.output
    except Exception as e:
        print(f"Error processing request: {e}")
        return "We're sorry, we could not process your request right now. Please contact our sales team."


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        response = call_multi_agent_system(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()

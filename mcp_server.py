import os
import json
import pandas as pd
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Loading all CSV files
DATA_DIR = Path(__file__).parent / "data"

products  = pd.read_csv(DATA_DIR / "products.csv")
suppliers = pd.read_csv(DATA_DIR / "suppliers.csv")
orders    = pd.read_csv(DATA_DIR / "orders.csv")
shipments = pd.read_csv(DATA_DIR / "shipments.csv")

# Creating the MCP server
mcp = FastMCP("supply-chain-risk-server")

#Writing tools functionalities
@mcp.tool()
def get_order_details(order_id: str) -> str:

    order = orders[orders["order_id"] == order_id]
    if order.empty:
        return json.dumps({"error": f"Order '{order_id}' not found."})
  
    order_row = order.iloc[0]
    product_id = order_row["product_id"]

    product = products[products["product_id"] == product_id]
    product_name = product.iloc[0]["product_name"] if not product.empty else "Unknown"


    shipment = shipments[shipments["order_id"] == order_id]
    shipment_info = {}
    if not shipment.empty:
        s = shipment.iloc[0]
        shipment_info = {
            "shipment_id": s["shipment_id"],
            "shipment_status": s["status"],
            "delay_reason": s["reason"] if s["reason"] != "-" else None,
        }

    result = {
        "order_id": order_row["order_id"],
        "product_id": product_id,
        "product_name": product_name,
        "quantity": int(order_row["quantity"]),
        "order_status": order_row["status"],
        **shipment_info,
    }
    return json.dumps(result)

@mcp.tool()
def get_inventory(product_id: str) -> str:

    product = products[products["product_id"] == product_id]
    if product.empty:
        return json.dumps({"error": f" Product'{product_id}' Not Found "})
    
    product_name = product.iloc[0]["product_name"]
    product_stock=int(product.iloc[0]["current_stock"])
    supplier_id = product.iloc[0]["supplier_id"]
    supplier_name = suppliers[suppliers["supplier_id"] == supplier_id].iloc[0]["supplier_name"]
    reorders = int(product.iloc[0]["reorder_level"])
    result = {
        "product_name": product_name,
        "stock": product_stock,
        "supplier name": supplier_name,
        "reorder count": reorders
    }

    return json.dumps(result)

@mcp.tool()
def get_supplier_details(product_id: str) -> str:
    product = products[products["product_id"] == product_id]
    if product.empty:
        return json.dumps({"error": f"Product '{product_id}' not found."})
    
    product_row = product.iloc[0]
    supplier_id = product_row["supplier_id"]

    supplier_row = suppliers[suppliers["supplier_id"] == supplier_id].iloc[0]
    name = supplier_row["supplier_name"]
    days = int(supplier_row["lead_time_days"])

    result = {
        "supplier_name": name,
        "supplier_id": supplier_id,
        "lead_time_days": days
    }

    return json.dumps(result)


@mcp.tool()
def get_delayed_shipments() ->str:
    delays = shipments[shipments["status"]=='Delayed']
    if delays.empty:
        return json.dumps({"message:", "No delayed shipments found"})
    
    result = []
    for _,rows in delays.iterrows():
        shipment_id = rows["shipment_id"]
        order_id=rows["order_id"]
        reason= rows["reason"]
        order = orders[orders["order_id"]==order_id]
        product_id= order.iloc[0].product_id
        product = products[products["product_id"] == product_id]
        product_name = product.iloc[0]["product_name"]

       

        result .append({
            "shipment_id": shipment_id,
            "order_id": order_id,
            "reason": reason,
            "product_id": product_id,
            "product_name": product_name
        })

    return json.dumps({"delays": result,"count": len(result)})

@mcp.tool()
def get_low_stock_products() -> str:
    low = products[products["current_stock"] < products["reorder_level"]]

    if low.empty:
        return json.dumps({"message": "All products are sufficiently stocked."})
    result = []
    for _, row in low.iterrows():
        result.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "current_stock": int(row["current_stock"]),
            "reorder_level": int(row["reorder_level"]),
            "deficit": int(row["reorder_level"]) - int(row["current_stock"])
        })

    return json.dumps({"low_stock_products": result, "count": len(result)})


@mcp.tool()
def recommend_reorder(product_id: str) -> str:
    product = products[products["product_id"] == product_id]
    if product.empty:
        return json.dumps({"error": f"Product '{product_id}' not found."})

    row = product.iloc[0]
    current = int(row["current_stock"])
    reorder_level = int(row["reorder_level"])
    supplier_id = row["supplier_id"]

    supplier = suppliers[suppliers["supplier_id"] == supplier_id]
    supplier_name = supplier.iloc[0]["supplier_name"]
    lead_time = int(supplier.iloc[0]["lead_time_days"])

    result = {
        "product_name": row["product_name"],
        "current_stock": current,
        "reorder_level": reorder_level,
        "needs_reorder": current < reorder_level,
        "supplier_name": supplier_name,
        "lead_time_days": lead_time
    }

    return json.dumps(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", port=port)
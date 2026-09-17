from fastmcp import FastMCP
import httpx

# Initialize Currency MCP Server
mcp = FastMCP("Currency Converter Server")

# Exchange Rates relative to 1 SGD
# RATES_TO_SGD = {
#     "INR": 0.016,  # ~1 INR = 0.016 SGD
#     "USD": 1.34,   # ~1 USD = 1.34 SGD
#     "EUR": 1.45,   # ~1 EUR = 1.45 SGD
#     "GBP": 1.70,   # ~1 GBP = 1.70 SGD
#     "SGD": 1.0
# }

@mcp.tool()
async def convert_currency(amount: float, from_currency: str, to_currency: str = "SGD") -> str:
    """
    Converts monetary amounts between live international currencies.
    To be used when user asks anything related to currency conversion or budget.
    """
    from_curr = from_currency.upper().strip()
    to_curr = to_currency.upper().strip()

    url = f"https://open.er-api.com/v6/latest/{from_curr}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        if data.get("result") != "success":
            return f"Error: Currency {from_curr} not supported or API unavailable."

        rates = data.get("rates", {})
        if to_curr not in rates:
            return f"Error: Target currency {to_curr} not found."

        rate = rates[to_curr]
        converted = amount * rate

        return (
            f"=== CURRENCY CONVERSION RESULT (Source: MCP Currency Tool) ===\n"
            f"Input: {amount:,.2f} {from_curr}\n"
            f"Converted: {converted:,.2f} {to_curr}\n"
            f"Exchange Rate: 1 {from_curr} = {rate:.4f} {to_curr}"
        )

    except Exception as e:
        return f"Error performing currency conversion: {str(e)}"

    # if from_curr not in RATES_TO_SGD or to_curr not in RATES_TO_SGD:
    #     return f"Error: Unsupported currency conversion. Supported units: {list(RATES_TO_SGD.keys())}"

    # # Calculate standard conversion
    # amount_in_sgd = amount * RATES_TO_SGD[from_curr]
    # converted_amount = amount_in_sgd / RATES_TO_SGD[to_curr]

    # return (
    #     f"=== CURRENCY CONVERSION RESULT (Source: MCP Currency Tool) ===\n"
    #     f"Input: {amount:,.2f} {from_curr}\n"
    #     f"Converted: {converted_amount:,.2f} {to_curr}\n"
    #     f"Exchange Rate Baseline: 1 {from_curr} = {RATES_TO_SGD[from_curr] / RATES_TO_SGD[to_curr]:.4f} {to_curr}"
    # )

if __name__ == "__main__":
    mcp.run(transport="stdio")
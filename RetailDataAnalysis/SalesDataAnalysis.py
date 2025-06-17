import psycopg2
import os
import re
import pandas as pd
from langchain.tools import tool
from urllib.parse import quote_plus
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub


import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas.io.sql")



custom_prompt_str = '''
You are a Helpful assistant who can create SQL Query Keeping in mind the database is in postgresql.
You can create the SImple as well as the complex Queries as well. Below are the tables-
- dim_products
- fact_order_line
- fact_aggregate

Also Below is the table structure and there fields - 
dim_products -
        product_name text  - This field has the item name 
        product_id bigint  - This field has the product ID or SKU ID
        category text      - This field has the product Catagory
        "price_INR" bigint - This field has the product Price in INR
        "price_USD" double precision -- This field has the product Price in USD

fact_order_line -
        order_id text               - This Holds the Order number
        order_placement_date date   - This holds the order Placement date
        customer_id bigint          - This HOlds the customer id
        product_id bigint           - This holds the Product ID or customer ID 
        order_qty bigint            - This holds the ordered Quantity of that line
        agreed_delivery_date date   - This holds the promise date
        actual_delivery_date date   - This holds the actual delivery date
        delivery_qty bigint         - This holds how many quantity has been shipped
        "In Full" text              - Is the order shipped fully or there is a cancellation (Partial/Full) 
        "On Time" text              - This holds the order fulfilled on time or not
        "On Time In Full" text      -This holds the order fulfilled on time or not, and all the quantity shipped fully or not

fact_aggregate -
        order_id text               - This Holds the Order number 
        customer_id bigint          - Customer ID
        order_placement_date date   - Order placed date
        on_time bigint              - If the order delivered on time 
        in_full text                - If the order shipped fully or partial of the order fulfilled 
        otif text                   - On time %

Relation between the tables-
dim_products has an One to One relationship with fact_order_line on product_id
fact_order_line has an One to One relationship with fact_aggregate on order_id

Rules:
        - Only give the output in a SQL formet that is ready to run.
        - Do not include any other tables and columns other that that.
        - All the dates are in YYYY-MM-DD format and are in Date datatype

Input: Give me the orders placed for item 25891503
Output: SELECT 
    fol.order_id,
    fol.order_placement_date,
    fol.customer_id,
    fol.order_qty,
    fol.agreed_delivery_date,
    fol.actual_delivery_date,
    fol.delivery_qty,
    fol."In Full",
    fol."On Time",
    fol."On Time In Full"
FROM 
    fact_order_line fol
JOIN 
    dim_products dp ON fol.product_id = dp.product_id
WHERE 
    dp.product_id = 25891503;


'''

prompt = ChatPromptTemplate(
    [
        ("system",custom_prompt_str),
        ("user","{input}" )
    ]
)
#print(prompt.input_variables)
#print(prompt.output_parser)

# Supabase connection details


def createSupabaseConnection():

    conn = psycopg2.connect(
        host="",
        port="",
        dbname="",
        user="",
        password="",
        sslmode="require"  # Very important for Supabase
    )
    #print("conn -->", conn)
    return conn

def extract_sql_from_text(text: str) -> str:
    """
    Extracts the first SQL code block from the LLM response.
    """
    match = re.search(r"```sql\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        # Fallback: return everything from SELECT onward
        select_pos = text.lower().find("select")
        return text[select_pos:].strip() if select_pos != -1 else text

@tool
def executeQuery(query: str):
    '''
    This function used to fetch all data based on the query
    '''
    final_query = extract_sql_from_text(query)
    conn = createSupabaseConnection()
    #print("Query from executeQuery -->", query)
    df = pd.read_sql(final_query, conn)
    conn.close()
    #return df
    return df.to_markdown(index=False, tablefmt="retaildata")


tools = [executeQuery]
prompt_hub = hub.pull("hwchase17/react")

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", temperature=0)
user_query = "Show me all the orders which shipped in full also shipped in time"


agent = create_react_agent(
    llm=llm,
    tools = tools,
    prompt= prompt_hub
)

agent_executor = AgentExecutor(
    agent = agent,
    tools= tools,
    verbose=False
)

#looping for Questions - Starts
while(True):
    user_query = input(">")
    if(user_query == "Exit"):
        break;
    response = prompt | llm
    output=response.invoke({"input":{user_query}})
    query_output = extract_sql_from_text(output.content)

    final_input = f"""
    User Question: {user_query}
    Query to Execute: {query_output}
    """
    print(query_output)


    response = agent_executor.invoke({"input":final_input})
    print(response["output"])
#Looping for Questions - Ends












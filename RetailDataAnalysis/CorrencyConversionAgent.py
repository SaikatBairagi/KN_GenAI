from langchain_community.tools import tool
from langchain_openai import ChatOpenAI
from langchain import hub
from dotenv import load_dotenv
import os
import requests
from langchain.agents import  Tool, initialize_agent
from langchain.agents.agent import AgentType

load_dotenv()
currency_key = os.getenv("CURRENCY_CONVERSION_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")
os.environ["LANGCHAIN_TRACING_V2"] = "true"


def currencyConverter(string):
    fromCurrency, toCurrency = string.split(",")
    return currencyConverter_helper(toCurrency, fromCurrency)

def convertion(string):
    amount, convertionRate = string.split(",")
    return convertion_helper(float(amount), float(convertionRate))


def currencyConverter_helper(toCurrency: str, fromCurrency: str) -> dict:
    '''
    This function fetch the currenct conversion factor between the base currency and the target currency
    This function accepts two Input as below-
    toCurrency as String    - This will be the currency code to which it will be converted
    fromCurrenct as String  - This will be the currency code from which it will be converted
    
    '''
   
    url = f"https://apilayer.net/api/live?access_key={currency_key}&currencies={toCurrency}&source={fromCurrency}&format=1"
    print(url)
    response=requests.get(url)
    return response.json()


def convertion_helper(amount : int, convertionRate : float) -> float :
    '''This function returns the product of amount given with the conversion rate'''
    print(type(amount),"-->",type(convertionRate))
    return round(amount * convertionRate,2)

llm = ChatOpenAI(model="gpt-4o")
prompt_hub = hub.pull("hwchase17/react-multi-input-json")
tools = [
    Tool(
        name = "convertion",
        func=convertion,
        description="useful for when you need to multiply two numbers together. The input to this tool should be a comma separated list of numbers of length two, representing the two numbers you want to multiply together. For example, `1,2` would be the input if you wanted to multiply 1 by 2."
    ),
    Tool(
        name = "currencyConverter",
        func=currencyConverter,
        description='''useful for when you need to know the 2 currenct that needs to be converted from one to another. The input to this tool should be a comma separated list of String of length two, representing the two String you want to convert'''
    )
]


agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

while(True):
    user_query = input("> ")
    if(user_query == "Exit"):
        break;
    response = agent.invoke({"input":user_query})
    print("🤖 ",response["output"])


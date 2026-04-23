from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import inventory_bot as sql_bot
import knowledge_agent as neo_bot
import os

app = FastAPI(title="NEXUS AI API")

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"

@app.get("/")
def home():
    return {"status": "online", "message": "NEXUS AI API is running"}

@app.post("/sql/query")
def query_sql(request: QueryRequest):
    try:
        # Load memory for session
        history = sql_bot.load_memory(request.session_id)
        
        # SQL Workflow
        sql = sql_bot.generator_node(request.query, history)
        results = sql_bot.executor_node(sql)
        
        if results["status"] == "error":
            sql = sql_bot.corrector_node(sql, results["message"])
            results = sql_bot.executor_node(sql)
            
        if results["status"] == "success":
            answer = sql_bot.responder_node(request.query, results["data"])
            sql_bot.save_memory(request.query, answer, request.session_id)
            eval_res = sql_bot.evaluation_node(request.query, sql, results["data"], answer)
            
            return {
                "response": answer,
                "sql": sql,
                "evaluation": eval_res
            }
        else:
            raise HTTPException(status_code=500, detail=results["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/graph/query")
def query_graph(request: QueryRequest):
    # This would require modifying knowledge_agent.py to be more modular 
    # but for now we call the logic directly
    agent = neo_bot.Neo4jAgent()
    try:
        history = agent.load_memory()
        intent = neo_bot.classifier_node(request.query)
        cypher = neo_bot.cypher_generator_node(request.query, history)
        res = agent.execute_cypher(cypher)
        
        if res["status"] == "success":
            ans = f"Action processed. Data: {res['data']}"
            agent.save_memory(request.query, ans)
            ev = neo_bot.evaluation_node(request.query, cypher, res["data"], ans)
            return {"response": ans, "cypher": cypher, "evaluation": ev}
        else:
            raise HTTPException(status_code=500, detail=res["message"])
    finally:
        agent.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

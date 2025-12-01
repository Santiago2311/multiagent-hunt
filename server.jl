using Genie, Genie.Router, Genie.Renderer.Json, Genie.Requests

include("game.jl")

route("/") do
    return "Multi-agent Hunt Game Server"
end

route("/simulate", method = POST) do
    simulate_step()
    state = get_model_state()
    return json(Dict("status" => "step executed", "state" => state))
end

route("/state", method = GET) do
    state = get_model_state()
    return json(state)
end

# NEW: Step a specific agent by ID
route("/agent/:id/step", method = POST) do
    agent_id = parse(Int, payload(:id))
    try
        step_agent_by_id(agent_id)
        agent_state = get_agent_state(agent_id)
        return json(Dict("status" => "agent stepped", "agent" => agent_state))
    catch e
        return json(Dict("error" => "Agent not found or error: $e"), status = 404)
    end
end

# NEW: Get specific agent's state
route("/agent/:id", method = GET) do
    agent_id = parse(Int, payload(:id))
    try
        agent_state = get_agent_state(agent_id)
        return json(agent_state)
    catch e
        return json(Dict("error" => "Agent not found: $e"), status = 404)
    end
end

route("/human/position", method = POST) do
    try
        body = Genie.Requests.jsonpayload()
        grid_x = body["x"]
        grid_y = body["y"]
        new_pos = (grid_x, grid_y)
        
        success = update_human_position(new_pos)
        if success
            human_state = get_agent_state(9)
            return json(Dict("status" => "position updated", "human" => human_state))
        else
            return json(Dict("error" => "Invalid position"), status = 400)
        end
    catch e
        println("Error updating human position: $e")
        return json(Dict("error" => "Failed to update position: $e"), status = 400)
    end
end

Genie.config.run_as_server = true
Genie.config.cors_headers["Access-Control-Allow-Origin"] = "*"
Genie.config.cors_headers["Access-Control-Allow-Headers"] = "Content-Type"
Genie.config.cors_headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
Genie.config.cors_allowed_origins = ["*"]

up()

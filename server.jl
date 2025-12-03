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

# Step a specific agent by ID
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

# Get specific agent's state
route("/agent/:id", method = GET) do
    agent_id = parse(Int, payload(:id))
    try
        agent_state = get_agent_state(agent_id)
        return json(agent_state)
    catch e
        return json(Dict("error" => "Agent not found: $e"), status = 404)
    end
end

# Update human position
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

# Human fixes a generator
route("/human/fix", method = POST) do
    try
        body = Genie.Requests.jsonpayload()
        generator_id = Int(body["generatorId"])
        success, result = human_try_fix_generator(generator_id)
        if success
            generator = result
            generator_state = get_agent_state(generator.id)
            state = get_model_state()
            return json(Dict(
                "status" => "fixing",
                "generator" => generator_state,
                "state" => state
            ))
        else
            return json(Dict("error" => result), status = 400)
        end
    catch e
        println("Error fixing generator: $e")
        return json(Dict("error" => "Failed to process fix request: $e"), status = 400)
    end
end

# Get human position
route("/human/position", method = GET) do
    try
        pos = get_human_position()
        if pos !== nothing
            return json(Dict("pos" => [pos[1], pos[2]]))
        else
            return json(Dict("error" => "Human not found"), status = 404)
        end
    catch e
        println("Error getting human position: $e")
        return json(Dict("error" => "Failed to get position: $e"), status = 400)
    end
end

Genie.config.run_as_server = true
Genie.config.cors_headers["Access-Control-Allow-Origin"] = "*"
Genie.config.cors_headers["Access-Control-Allow-Headers"] = "Content-Type"
Genie.config.cors_headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
Genie.config.cors_allowed_origins = ["*"]

up()

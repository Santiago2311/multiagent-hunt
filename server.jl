using Genie, Genie.Router, Genie.Renderer.Json

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

Genie.config.run_as_server = true
Genie.config.cors_headers["Access-Control-Allow-Origin"] = "*"
Genie.config.cors_headers["Access-Control-Allow-Headers"] = "Content-Type"
Genie.config.cors_headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
Genie.config.cors_allowed_origins = ["*"]

up()
using Agents
using Random


mutable struct DoorAgent <: AbstractAgent
    id::Int
    pos::NTuple{2, Int}
    isOpen::Bool
end

mutable struct GeneratorAgent <: AbstractAgent
    id::Int
    pos::NTuple{2, Int}
    timeToFix::Int
    isFixed::Bool
end

mutable struct EscapistAgent <: AbstractAgent
    id::Int
    pos::NTuple{2, Int}
    fixingSpeed::Int
    hasEscaped::Bool
    knowsExitLocation::Bool
    exitLocation::Union{Nothing, NTuple{2, Int}}
end

mutable struct SaboteurAgent <: AbstractAgent
    id::Int
    pos::NTuple{2, Int}
    speed::Int
    controlledDoors::Vector{Int}
end

mutable struct HumanAgent <: AbstractAgent
    id::Int
    pos::NTuple{2, Int}
    fixingSpeed::Int
    hasEscaped::Bool
    knowsExitLocation::Bool
    exitLocation::Union{Nothing, NTuple{2, Int}}
end

const GRID_DIMS = (13, 13)

const MAZE = [
    1 1 1 1 1 1 0 1 1 1 1 1 1;
    1 0 0 0 0 1 0 0 0 0 1 0 1;
    1 0 0 1 0 0 0 1 1 0 0 0 1;
    1 0 1 1 0 0 1 0 0 0 1 1 1;
    1 0 0 0 0 1 0 0 1 0 0 0 1;
    1 0 1 0 1 1 1 1 1 0 0 0 1;
    1 0 1 1 1 0 0 0 1 1 0 0 1;
    1 0 0 0 1 0 0 0 0 0 0 1 1;
    1 1 0 1 1 0 0 0 1 0 0 1 1;
    1 0 0 0 0 1 1 1 0 0 0 0 1;
    1 0 1 1 1 1 0 0 0 1 1 0 1;
    1 0 0 0 0 0 0 1 0 1 0 0 1;
    1 1 1 1 1 1 1 1 1 1 1 1 1
]

# spawn safe zone
const SPAWN_POS = (7, 8)
const SAFE_RADIUS = 1
in_safe_zone(pos::NTuple{2,Int}) = abs(pos[1] - SPAWN_POS[1]) <= SAFE_RADIUS && abs(pos[2] - SPAWN_POS[2]) <= SAFE_RADIUS

function is_walkable(pos::NTuple{2, Int})
    x, y = pos
    if !(1 <= x <= GRID_DIMS[1] && 1 <= y <= GRID_DIMS[2])
        return false
    end
    return MAZE[y, x] == 0
end

function manhattan_distance(p1::NTuple{2, Int}, p2::NTuple{2, Int})
    abs(p1[1] - p2[1]) + abs(p1[2] - p2[2])
end

function is_adjacent(p1::NTuple{2, Int}, p2::NTuple{2, Int})
    manhattan_distance(p1, p2) == 1
end

function get_neighbors(pos::NTuple{2, Int}, model)
    candidates = ((pos[1] + 1, pos[2]),
                  (pos[1] - 1, pos[2]),
                  (pos[1], pos[2] + 1),
                  (pos[1], pos[2] - 1))
    neighbors = NTuple{2, Int}[]
    for new_pos in candidates
        if is_walkable(new_pos)
            push!(neighbors, new_pos)
        end
    end
    return neighbors
end

function random_walk!(agent::EscapistAgent, model)
    neighbors = get_neighbors(agent.pos, model)
    if !isempty(neighbors)
        new_pos = rand(neighbors)
        move_agent!(agent, new_pos, model)
    end
end

function move_towards_target!(agent, target::NTuple{2, Int}, model)
    current = agent.pos
    if current == target
        return
    end
    
    neighbors = get_neighbors(current, model)
    if isempty(neighbors)
        return
    end
    
    best_neighbor = neighbors[1]
    best_distance = manhattan_distance(best_neighbor, target)
    
    for neighbor in neighbors[2:end]
        dist = manhattan_distance(neighbor, target)
        if dist < best_distance
            best_distance = dist
            best_neighbor = neighbor
        end
    end
    
    move_agent!(agent, best_neighbor, model)
end

function count_unfixed_generators(model)
    count = 0
    for agent in allagents(model)
        if agent isa GeneratorAgent && !agent.isFixed
            count += 1
        end
    end
    return count
end

function all_generators_fixed(model)
    return count_unfixed_generators(model) == 0
end

function inform_exit_location!(exit_pos::NTuple{2, Int}, model)
    for agent in allagents(model)
        if agent isa EscapistAgent && !agent.hasEscaped
            agent.knowsExitLocation = true
            agent.exitLocation = exit_pos
        elseif agent isa HumanAgent && !agent.hasEscaped
            agent.knowsExitLocation = true
            agent.exitLocation = exit_pos
        end
    end
end

function agent_step!(agent::EscapistAgent, model)
    if agent.hasEscaped
        return
    end
    
    unfixed_count = count_unfixed_generators(model)
    
    if unfixed_count == 0
        if agent.knowsExitLocation && agent.exitLocation !== nothing
            move_towards_target!(agent, agent.exitLocation, model)
            
            exit_door = nothing
            for a in allagents(model)
                if a isa DoorAgent && a.pos == agent.exitLocation
                    exit_door = a
                    break
                end
            end
            
            if exit_door !== nothing && agent.pos == exit_door.pos && exit_door.isOpen
                agent.hasEscaped = true
                println("Escapist $(agent.id) has escaped!")
            end
        else
            random_walk!(agent, model)
            
            for a in allagents(model)
                if a isa DoorAgent && is_adjacent(agent.pos, a.pos)
                    println("Escapist $(agent.id) found the exit! Informing others...")
                    inform_exit_location!(a.pos, model)
                    break
                end
            end
        end
    else
        random_walk!(agent, model)
        
        for a in allagents(model)
            if a isa GeneratorAgent && !a.isFixed && is_adjacent(agent.pos, a.pos)
                a.timeToFix -= agent.fixingSpeed
                println("Escapist $(agent.id) is fixing Generator $(a.id). Time left: $(a.timeToFix)")
                
                if a.timeToFix <= 0
                    a.isFixed = true
                    println("Generator $(a.id) is now fixed! Generators left: $(count_unfixed_generators(model))")
                    
                    if all_generators_fixed(model)
                        for door_agent in allagents(model)
                            if door_agent isa DoorAgent
                                door_agent.isOpen = true
                                println("Exit door $(door_agent.id) is now open!")
                            end
                        end
                    end
                end
                break
            end
        end
    end
end

function agent_step!(agent::SaboteurAgent, model)
    nearest_target = nothing
    min_distance = Inf
    
    for a in allagents(model)
        if (a isa EscapistAgent && !a.hasEscaped && !in_safe_zone(a.pos)) || 
           (a isa HumanAgent && !a.hasEscaped && !in_safe_zone(a.pos))
            dist = manhattan_distance(agent.pos, a.pos)
            if dist < min_distance
                min_distance = dist
                nearest_target = a
            end
        end
    end
    
    if nearest_target !== nothing
        if is_adjacent(agent.pos, nearest_target.pos)
            if nearest_target isa EscapistAgent
                println("Saboteur $(agent.id) caught Escapist $(nearest_target.id)!")
            elseif nearest_target isa HumanAgent
                println("Saboteur $(agent.id) caught Human Player $(nearest_target.id)!")
            end
            move_agent!(nearest_target, SPAWN_POS, model)
        else
            move_towards_target!(agent, nearest_target.pos, model)
        end
    end
end

function agent_step!(agent::GeneratorAgent, model)
end

function agent_step!(agent::DoorAgent, model)
end

function agent_step!(agent::HumanAgent, model)
end


space = GridSpace(GRID_DIMS; periodic = false, metric = :manhattan)

model = ABM(Union{DoorAgent, GeneratorAgent, EscapistAgent, SaboteurAgent, HumanAgent}, space; agent_step! = agent_step!, warn = false)

@assert is_walkable(SPAWN_POS) "Spawn point must be on a walkable cell"

exit_door = DoorAgent(1, (12, 12), false)
@assert is_walkable(exit_door.pos) "Exit door must be on a walkable cell"
add_agent_own_pos!(exit_door, model)

gen1 = GeneratorAgent(2, (3, 5), 5, false)
@assert is_walkable(gen1.pos)
add_agent_own_pos!(gen1, model)

gen2 = GeneratorAgent(3, (8, 7), 5, false)
@assert is_walkable(gen2.pos)
add_agent_own_pos!(gen2, model)

gen3 = GeneratorAgent(4, (11, 8), 5, false)
@assert is_walkable(gen3.pos)
add_agent_own_pos!(gen3, model)

esc1 = EscapistAgent(5, (2, 2), 1, false, false, nothing)
@assert is_walkable(esc1.pos)
add_agent_own_pos!(esc1, model)

esc2 = EscapistAgent(6, (2, 4), 1, false, false, nothing)
@assert is_walkable(esc2.pos)
add_agent_own_pos!(esc2, model)

esc3 = EscapistAgent(7, (4, 2), 1, false, false, nothing)
@assert is_walkable(esc3.pos)
add_agent_own_pos!(esc3, model)

sab1 = SaboteurAgent(8, (10, 10), 1, [exit_door.id])
@assert is_walkable(sab1.pos)
add_agent_own_pos!(sab1, model)

human = HumanAgent(9, SPAWN_POS, 1, false, false, nothing)
@assert is_walkable(human.pos)
add_agent_own_pos!(human, model)

# Step individual agent by ID
function step_agent_by_id(agent_id::Int)
    agent = model[agent_id]
    agent_step!(agent, model)
end

function simulate_step()
    step!(model)
end

function get_model_state()
    state = Dict(
        "escapists" => [],
        "generators" => [],
        "saboteurs" => [],
        "doors" => []
    )
    
    for agent in allagents(model)
        if agent isa EscapistAgent
            push!(state["escapists"], Dict(
                "id" => agent.id,
                "pos" => agent.pos,
                "hasEscaped" => agent.hasEscaped,
                "knowsExit" => agent.knowsExitLocation
            ))
        elseif agent isa GeneratorAgent
            push!(state["generators"], Dict(
                "id" => agent.id,
                "pos" => agent.pos,
                "isFixed" => agent.isFixed,
                "timeToFix" => agent.timeToFix
            ))
        elseif agent isa SaboteurAgent
            push!(state["saboteurs"], Dict(
                "id" => agent.id,
                "pos" => agent.pos
            ))
        elseif agent isa DoorAgent
            push!(state["doors"], Dict(
                "id" => agent.id,
                "pos" => agent.pos,
                "isOpen" => agent.isOpen
            ))
        elseif agent isa HumanAgent
            state["human"] = Dict(
                "id" => agent.id,
                "pos" => agent.pos,
                "hasEscaped" => agent.hasEscaped,
                "knowsExit" => agent.knowsExitLocation
            )
        end
    end
    
    return state
end

# Get specific agent's state
function get_agent_state(agent_id::Int)
    agent = model[agent_id]
    
    if agent isa EscapistAgent
        return Dict(
            "type" => "escapist",
            "id" => agent.id,
            "pos" => agent.pos,
            "hasEscaped" => agent.hasEscaped,
            "knowsExit" => agent.knowsExitLocation
        )
    elseif agent isa GeneratorAgent
        return Dict(
            "type" => "generator",
            "id" => agent.id,
            "pos" => agent.pos,
            "isFixed" => agent.isFixed,
            "timeToFix" => agent.timeToFix
        )
    elseif agent isa SaboteurAgent
        return Dict(
            "type" => "saboteur",
            "id" => agent.id,
            "pos" => agent.pos
        )
    elseif agent isa DoorAgent
        return Dict(
            "type" => "door",
            "id" => agent.id,
            "pos" => agent.pos,
            "isOpen" => agent.isOpen
        )
    elseif agent isa HumanAgent
        return Dict(
            "type" => "human",
            "id" => agent.id,
            "pos" => agent.pos,
            "hasEscaped" => agent.hasEscaped,
            "knowsExit" => agent.knowsExitLocation
        )
    end
end

function update_human_position(new_pos::NTuple{2, Int})
    human = model[9]
    if human isa HumanAgent
        if is_walkable(new_pos)
            move_agent!(human, new_pos, model)
            return true
        end
    end
    return false
end

function get_human_position()
    human = model[9]
    if human isa HumanAgent
        return human.pos
    end
    return nothing
end

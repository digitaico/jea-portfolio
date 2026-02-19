-- Vim Ollama Agent for Vim 9.2 (Standard Vim)
-- Finalized for compatibility with Vim 9.2 Lua interface.

local M = {}
_G.OllamaAgent = M -- Make accessible to Vimscript bridge

-- State Management
M.state = {
    config_path = vim.fn.expand("~/.config/vim/local_slm_roles.yaml"),
    roles = {},
    current_role_name = "code",
    active_job = nil,
    active_output = "",
    active_callback = nil,
    suggestion = nil,
    popup_id = nil,
    prop_type = "OllamaGhostText"
}

-- Initialize Text Properties for Ghost Text
if vim.fn.prop_type_get(M.state.prop_type) == {} then
    vim.fn.prop_type_add(M.state.prop_type, { highlight = "Comment" })
end

--------------------------------------------------------------------------------
-- Dynamic YAML Parser (Handles: key: &anchor "value" and key: *alias)
--------------------------------------------------------------------------------
local function parse_yaml(path)
    if vim.fn.filereadable(path) == 0 then return nil end
    local raw_lines = vim.fn.readfile(path)
    local lines = {}
    for i = 1, #raw_lines do table.insert(lines, raw_lines[i]) end
    
    local anchors = {}
    local roles = {}
    
    local function super_clean(s)
        if not s then return "" end
        -- Remove quotes and surrounding whitespace
        local cleaned = s:gsub('"', ''):gsub("'", '')
        cleaned = cleaned:gsub("^%s+", ""):gsub("%s+$", "")
        return cleaned
    end

    -- Pass 1: Global Anchor Collection
    for i = 1, #lines do
        local line = lines[i]
        -- Match key: &anchor "value" OR key: &anchor value
        local anchor, val = line:match("&([%w_]+)%s+(.*)$")
        if anchor then 
            anchors[anchor] = super_clean(val) 
        end
    end

    -- Pass 2: Role Extraction
    local in_roles = false
    local cur_role = nil
    local cur_key = nil

    for i = 1, #lines do
        local line = lines[i]
        if line:match("^roles:") then
            in_roles = true
        elseif in_roles then
            -- Role header (2 spaces)
            local r_name = line:match("^  ([%w_]+):")
            if r_name then
                cur_role = r_name
                roles[cur_role] = {}
                cur_key = nil
            elseif cur_role then
                -- Property (4 spaces)
                local k, v = line:match("^    ([%w_]+):%s*(.*)$")
                if k then
                    cur_key = k
                    -- Resolve aliases using literal asterisk escape %*
                    v = v:gsub("%%*([%w_]+)", function(a) return anchors[a] or "" end)
                    v = super_clean(v)
                    -- For endpoints, ensure no double slashes and no spaces
                    if cur_key == "endpoint" then
                        v = v:gsub("%s+", ""):gsub("([^:])//+", "%1/")
                    end
                    roles[cur_role][cur_key] = v
                elseif cur_key and line:match("^      ") then
                    -- Multi-line indentation (6 spaces)
                    local extra = line:gsub("^%s+", "")
                    extra = extra:gsub("%%*([%w_]+)", function(a) return anchors[a] or a end)
                    roles[cur_role][cur_key] = (roles[cur_role][cur_key] or "") .. " " .. super_clean(extra)
                end
            end
            -- End roles block on any non-indented line that isn't the header
            if #line > 0 and not line:match("^%s") and not line:match("^roles:") then
                in_roles = false
            end
        end
    end
    return roles
end

--------------------------------------------------------------------------------
-- Async API Execution (Bridge compatible with Vim 9.2)
--------------------------------------------------------------------------------

function M._handle_stdout(msg)
    M.state.active_output = M.state.active_output .. msg
end

function M._handle_exit()
    local output = M.state.active_output
    local callback = M.state.active_callback
    M.state.active_job = nil
    M.state.active_output = ""
    M.state.active_callback = nil

    local ok, decoded = pcall(vim.fn.json_decode, output)
    if ok and decoded then
        local result = ""
        if decoded.choices and decoded.choices[1] then
            local choice = decoded.choices[1]
            result = (choice.message and choice.message.content) or choice.text or ""
        elseif decoded.response then
            result = decoded.response
        end
        if callback then callback(result) end
    end
end

function M.request(prompt, suffix, callback)
    local role = M.state.roles[M.state.current_role_name] or {}
    if not role.model then 
        print("Ollama Error: Model not found for role '" .. M.state.current_role_name .. "'")
        return 
    end
    
    local endpoint = role.endpoint or "http://localhost:11434/v1/chat/completions"
    local temp = tonumber(role.temperature) or 0.2
    local max_t = tonumber(role.max_tokens) or 500

    -- Hardened JSON construction to avoid Vim 9.2 "cannot convert value" error
    local payload = ""
    if endpoint:match("chat") then
        payload = string.format(
            '{"model":%s,"temperature":%s,"max_tokens":%s,"stream":false,"messages":[{"role":"system","content":%s},{"role":"user","content":%s}]}',
            vim.fn.json_encode(role.model),
            tostring(temp),
            tostring(max_t),
            vim.fn.json_encode(role.prompt or ""),
            vim.fn.json_encode(prompt)
        )
    else
        payload = string.format(
            '{"model":%s,"temperature":%s,"max_tokens":%s,"stream":false,"prompt":%s,"suffix":%s}',
            vim.fn.json_encode(role.model),
            tostring(temp),
            tostring(max_t),
            vim.fn.json_encode((role.prompt or "") .. "\n\n" .. prompt),
            vim.fn.json_encode(suffix or "")
        )
    end

    local curl_cmd = "curl -s -X POST " .. endpoint .. 
                     " -H 'Content-Type: application/json' -d " .. 
                     vim.fn.shellescape(payload)

    if M.state.active_job then vim.fn.job_stop(M.state.active_job) end

    M.state.active_output = ""
    M.state.active_callback = callback
    
    -- Standard Vim job options using string names for callbacks
    local options = {
        out_cb = "OllamaOutBridge",
        exit_cb = "OllamaExitBridge"
    }
    
    M.state.active_job = vim.fn.job_start(curl_cmd, options)
end

--------------------------------------------------------------------------------
-- UI and Interaction
--------------------------------------------------------------------------------
function M.trigger_completion()
    if vim.fn.mode() ~= "i" then return end
    local col = vim.fn.col(".")
    local prefix = vim.fn.getline("."):sub(1, col - 1)
    
    M.request(prefix, "", function(result)
        if not result or result == "" then return end
        M.state.suggestion = result
        local cur_pos = vim.fn.screenpos(0, vim.fn.line("."), col)
        M.state.popup_id = vim.fn.popup_create(vim.fn.split(result, "\n"), {
            line = cur_pos.row, col = cur_pos.col,
            highlight = "Comment", padding = {0, 1, 0, 1}, fixed = 1
        })
    end)
end

function M.accept_completion()
    if not M.state.suggestion or M.state.suggestion == "" then return "\t" end
    local text = M.state.suggestion
    M.clean_ui()
    vim.fn.feedkeys(text, "n")
    return ""
end

function M.switch_role(name)
    if M.state.roles[name] then
        M.state.current_role_name = name
        print("Ollama Role: " .. name .. " [" .. (M.state.roles[name].model or "default") .. "]")
    else
        print("Role '" .. name .. "' not found.")
    end
end

function M.setup()
    -- Ensure roles are loaded
    M.state.roles = parse_yaml(M.state.config_path)

    -- Define Global Vimscript Bridge
    vim.command([[
        function! OllamaOutBridge(chan, msg)
            lua _G.OllamaAgent._handle_stdout(a:msg)
        endfunction
        function! OllamaExitBridge(chan, status)
            lua _G.OllamaAgent._handle_exit()
        endfunction
    ]])

    -- Register Commands
    vim.command("command! -nargs=1 OllamaRole lua _G.OllamaAgent.switch_role(<q-args>)")
    vim.command("command! OllamaChat lua _G.OllamaAgent.chat_prompt()")
    vim.command("command! OllamaDebug lua _G.OllamaAgent.debug_config()")

    -- Register Mappings
    vim.command("inoremap <silent> <C-g> <cmd>lua _G.OllamaAgent.trigger_completion()<CR>")
    vim.command("inoremap <silent> <expr> <Tab> luaeval(\"_G.OllamaAgent.accept_completion()\")")
    
    -- Autocmd for UI cleanup
    vim.command("augroup OllamaCleanup")
    vim.command("autocmd!")
    vim.command("autocmd CursorMoved,InsertLeave * lua _G.OllamaAgent.clean_ui()")
    vim.command("augroup END")
end

function M.clean_ui()
    if M.state.popup_id then vim.fn.popup_close(M.state.popup_id) M.state.popup_id = nil end
    vim.fn.prop_clear(1, vim.fn.line("$"))
    M.state.suggestion = nil
end

function M.chat_prompt()
    local input = vim.fn.input("Agent Ask [" .. M.state.current_role_name .. "]: ")
    if input == "" then return end
    print("\nOllama is thinking...")
    M.request(input, "", function(res)
        vim.command("vnew")
        local lines = vim.fn.split(res, "\n")
        -- Append lines one by one to avoid large-table conversion errors
        for i = 1, #lines do 
            vim.fn.append(vim.fn.line("$") - 1, lines[i]) 
        end
        vim.command("setlocal buftype=nofile filetype=markdown")
        print("Done.")
    end)
end

function M.debug_config()
    local keys = {}
    for k, _ in pairs(M.state.roles) do table.insert(keys, k) end
    print("YAML: " .. M.state.config_path)
    print("Roles: " .. table.concat(keys, ", "))
    local r = M.state.roles[M.state.current_role_name]
    if r then 
        print("Active: " .. M.state.current_role_name)
        print("Model: " .. tostring(r.model))
        print("Endpoint: " .. tostring(r.endpoint))
    end
end

return M
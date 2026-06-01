const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const port = process.env.PORT || 8084;

// Serve the index.html directly
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Mount the Repatch SDK from the parent SDK folder
app.get('/sdk/repatch-sdk.js', (req, res) => {
  res.sendFile(path.join(__dirname, '../../sdk/js/repatch-sdk.js'));
});

// Create HTTP server
const server = http.createServer(app);

// Initialize WebSocket server for repatch channel
const wss = new WebSocket.Server({ server, path: '/repatch' });

console.log(`\n%c[Repatch MCP Server] Starting evolutionary patch server...`, 'color: #a855f7; font-weight: bold;');

const PRESETS = {
  add_dashboard: `ADD #patch-workspace <div id="stats-widget" class="card" style="width: 100%; margin-top: 20px; background: rgba(59, 130, 246, 0.05); border-color: rgba(59, 130, 246, 0.2);"><div class="card-title">Live Transactions</div><p style="font-size: 2.5rem; font-weight: 800; color: #60a5fa; margin-bottom: 8px;">$14,290.00</p><p style="font-size: 0.85rem; color: #34d399;">+18.4% growth since last evolutionary patch</p></div>`,
  
  style_neon: `STYLE #stats-widget { background: rgba(236, 72, 153, 0.08); border-color: #ec4899; box-shadow: 0 0 20px rgba(236, 72, 153, 0.2); }`,
  
  replace_menu: `REPLACE #btn-explore <div id="control-bar" style="display:flex; gap: 12px; margin-top: 10px;"><button class="btn btn-primary" onclick="alert('Surgical evolution successfully processed via WebSocket MCP.')">Interactive Action</button></div>`,
  
  remove_baseline: `REMOVE #baseline-view`
};

wss.on('connection', (ws) => {
  console.log('[WS Connection] Client attached to Repatch streaming protocol.');

  // Send baseline confirmation
  ws.send(JSON.stringify({
    info: 'Connected to Repatch MCP patch channel.'
  }));

  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      let dslCommand = data.dsl || '';

      if (dslCommand.startsWith('TRIGGER_PRESET ')) {
        const presetName = dslCommand.replace('TRIGGER_PRESET ', '').trim();
        const presetDsl = PRESETS[presetName];
        if (presetDsl) {
          console.log(`[Preset Triggered] Simulating LLM evolution: ${presetName}`);
          broadcast({ dsl: presetDsl });
        } else {
          console.warn(`[Preset Error] Unknown preset: ${presetName}`);
        }
      } else if (dslCommand) {
        console.log(`[Manual DSL Broadcast] Broadcasting patch: ${dslCommand}`);
        broadcast({ dsl: dslCommand });
      }
    } catch (err) {
      console.error('[WS Error] Failed to parse message:', err);
    }
  });

  ws.on('close', () => {
    console.log('[WS Connection] Client disconnected.');
  });
});

function broadcast(payload) {
  const serialized = JSON.stringify(payload);
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(serialized);
    }
  });
}

server.listen(port, '0.0.0.0', () => {
  console.log(`\n======================================================`);
  console.log(`  Repatch MCP+WS Realtime Evolution demo is active!`);
  console.log(`  Local URL: http://localhost:${port}`);
  console.log(`======================================================\n`);
});

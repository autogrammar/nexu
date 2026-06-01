/**
 * Repatch Client-Side SDK (v1.0.0)
 * Enables surgical, real-time UI patching via WebSocket/SSE and DSL commands.
 */
class RepatchSDK {
  constructor(options = {}) {
    this.url = options.url || `ws://${window.location.host}/repatch`;
    this.protocol = options.protocol || 'ws'; // 'ws' or 'sse'
    this.listeners = [];
    this.connection = null;
    this._logStyleDsl = 'color: #a855f7; font-weight: bold; background: #2e1065; padding: 2px 6px; border-radius: 4px;';
    this._logStyleAction = 'color: #10b981; font-weight: bold;';
  }

  /**
   * Initialize and connect to the patch server.
   */
  connect() {
    console.log('%c[Repatch SDK] Initializing UI patch stream...', 'color: #3b82f6; font-weight: bold;');
    
    if (this.protocol === 'sse') {
      this._connectSSE();
    } else {
      this._connectWS();
    }
  }

  _connectWS() {
    this.connection = new WebSocket(this.url);

    this.connection.onopen = () => {
      console.log('%c[Repatch SDK] Connected to WebSockets patch stream', 'color: #10b981; font-weight: bold;');
    };

    this.connection.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.dsl) {
          this.apply(payload.dsl);
        }
      } catch (err) {
        console.error('[Repatch SDK] Message parse error:', err);
      }
    };

    this.connection.onclose = () => {
      console.warn('[Repatch SDK] WebSocket stream disconnected. Retrying in 3s...');
      setTimeout(() => this._connectWS(), 3000);
    };
  }

  _connectSSE() {
    this.connection = new EventSource(this.url);

    this.connection.onopen = () => {
      console.log('%c[Repatch SDK] Connected to SSE patch stream', 'color: #10b981; font-weight: bold;');
    };

    this.connection.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.dsl) {
          this.apply(payload.dsl);
        }
      } catch (err) {
        console.error('[Repatch SDK] SSE parse error:', err);
      }
    };

    this.connection.onerror = (err) => {
      console.error('[Repatch SDK] SSE connection failed. Reconnecting...', err);
    };
  }

  /**
   * Register a callback to run whenever a patch is applied.
   */
  onPatch(callback) {
    this.listeners.push(callback);
  }

  /**
   * Surgical execution of Repatch DSL commands:
   *   ADD <selector> <html_content>
   *   REPLACE <selector> <html_content>
   *   STYLE <selector> { css }
   *   REMOVE <selector>
   */
  apply(dslString) {
    const dslClean = dslString.trim();
    console.log(`%c[Repatch DSL]%c ${dslClean}`, this._logStyleDsl, 'color: #e2e8f0; font-family: monospace;');

    const addMatch = dslClean.match(/^ADD\s+([^\s]+)\s+([\s\S]+)$/i);
    const replaceMatch = dslClean.match(/^REPLACE\s+([^\s]+)\s+([\s\S]+)$/i);
    const styleMatch = dslClean.match(/^STYLE\s+([^\s]+)\s*\{([\s\S]+)\}$/i);
    const removeMatch = dslClean.match(/^REMOVE\s+([^\s]+)$/i);

    let action = '';
    let selector = '';

    try {
      if (addMatch) {
        selector = addMatch[1];
        const html = addMatch[2];
        const target = document.querySelector(selector);
        if (target) {
          target.insertAdjacentHTML('beforeend', html);
          action = 'ADD';
          console.log(`%c[Repatch Action] Appended child element to ${selector}`, this._logStyleAction);
        } else {
          throw new Error(`Target selector not found: ${selector}`);
        }
      } else if (replaceMatch) {
        selector = replaceMatch[1];
        const html = replaceMatch[2];
        const target = document.querySelector(selector);
        if (target) {
          target.innerHTML = html;
          action = 'REPLACE';
          console.log(`%c[Repatch Action] Replaced content of ${selector}`, this._logStyleAction);
        } else {
          throw new Error(`Target selector not found: ${selector}`);
        }
      } else if (styleMatch) {
        selector = styleMatch[1];
        const css = styleMatch[2].trim();
        const styleId = `repatch-style-${selector.replace(/[^a-zA-Z0-9]/g, '-')}`;
        let styleEl = document.getElementById(styleId);
        if (!styleEl) {
          styleEl = document.createElement('style');
          styleEl.id = styleId;
          document.head.appendChild(styleEl);
        }
        styleEl.textContent = `${selector} { ${css} }`;
        action = 'STYLE';
        console.log(`%c[Repatch Action] Applied scoped CSS rules to ${selector}`, this._logStyleAction);
      } else if (removeMatch) {
        selector = removeMatch[1];
        const target = document.querySelector(selector);
        if (target) {
          target.remove();
          action = 'REMOVE';
          console.log(`%c[Repatch Action] Surgically removed ${selector} from DOM`, this._logStyleAction);
        } else {
          throw new Error(`Target selector not found: ${selector}`);
        }
      } else {
        throw new Error('Unrecognized DSL command syntax.');
      }

      // Notify listeners
      this.listeners.forEach(cb => {
        try {
          cb({ success: true, dsl: dslClean, action, selector });
        } catch (e) {
          console.error('[Repatch SDK] Listener error:', e);
        }
      });

    } catch (error) {
      console.error(`%c[Repatch Error]%c Failed to apply patch: ${error.message}`, 'color: #ef4444; font-weight: bold;', 'color: #fda4af;');
      this.listeners.forEach(cb => {
        try {
          cb({ success: false, error: error.message, dsl: dslClean });
        } catch (e) {}
      });
    }
  }

  /**
   * Helper to send custom requests to the patch server.
   */
  sendPatchRequest(dslString) {
    if (this.connection && this.connection.readyState === WebSocket.OPEN) {
      this.connection.send(JSON.stringify({ dsl: dslString }));
    } else {
      console.warn('[Repatch SDK] Cannot send request, socket is not connected');
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = RepatchSDK;
} else {
  window.RepatchSDK = RepatchSDK;
}

// Injected bridge script. This text reaches the web layer as-is, so it must not
// name the wrapper. Native injects it with the trailing placeholder comment
// replaced by a JSON object:
// { "capabilities": string[], "runtimeVersion": string, "hosts": string[] }
(function (config) {
  'use strict';
  if (!config || window !== window.top || window.nativeBridge) return;
  if (!/^https?:$/.test(location.protocol) || config.hosts.indexOf(location.hostname) < 0) return;

  var android = window.nativeBridgeChannel;
  var ios = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.nativeBridgeChannel;
  var channel = android || ios;
  if (!channel) return;

  var seq = 0;
  var pending = {};
  var handlers = {};

  function post(message) {
    channel.postMessage(JSON.stringify(message));
  }

  function receive(raw) {
    var message;
    try {
      message = JSON.parse(raw);
    } catch (e) {
      return;
    }
    if (typeof message.id === 'string') {
      var resolve = pending[message.id];
      // Unknown ids are late replies addressed to a previous document.
      if (!resolve) return;
      delete pending[message.id];
      resolve(
        message.status === 'ok'
          ? { status: 'ok', data: message.data }
          : { status: message.status, code: message.code }
      );
    } else if (typeof message.event === 'string') {
      var list = handlers[message.event];
      if (!list) return;
      list.slice().forEach(function (handler) {
        try {
          handler(message.data);
        } catch (e) {
          setTimeout(function () { throw e; });
        }
      });
    }
  }

  if (android) {
    android.onmessage = function (event) { receive(event.data); };
  } else {
    Object.defineProperty(window, '__nativeBridgeReceive', { value: receive });
  }

  var bridge = {
    capabilities: Object.freeze(config.capabilities.slice()),
    runtimeVersion: config.runtimeVersion,
    call: function (method, params) {
      return new Promise(function (resolve) {
        var id = String(++seq);
        pending[id] = resolve;
        var message = { id: id, method: method };
        if (params !== undefined) message.params = params;
        try {
          post(message);
        } catch (e) {
          delete pending[id];
          resolve({ status: 'error', code: 'INTERNAL' });
        }
      });
    },
    on: function (event, handler) {
      (handlers[event] = handlers[event] || []).push(handler);
      return function () {
        var list = handlers[event];
        var index = list ? list.indexOf(handler) : -1;
        if (index >= 0) list.splice(index, 1);
      };
    }
  };
  Object.defineProperty(window, 'nativeBridge', { value: Object.freeze(bridge) });

  // Android can only push to the page through the reply proxy of a message the
  // page sent first, so announce the document as soon as it starts.
  post({ ready: true });
})(/*BRIDGE_CONFIG*/);

const [url, ...requests] = process.argv.slice(2);

if (!url || requests.length === 0) {
  console.error("usage: vscode-cdp.mjs <websocket-url> '<request-json>'...");
  process.exit(2);
}

const socket = new WebSocket(url);
const pending = new Set();
let nextId = 1;

const timeout = setTimeout(() => {
  console.error("CDP timeout");
  process.exit(1);
}, 15000);

socket.addEventListener("open", () => {
  for (const raw of requests) {
    const request = JSON.parse(raw);
    const id = nextId++;
    pending.add(id);
    socket.send(JSON.stringify({ id, ...request }));
  }
});

socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.id) {
    pending.delete(message.id);
    console.log(JSON.stringify(message));
    if (pending.size === 0) {
      clearTimeout(timeout);
      socket.close();
    }
  }
});

socket.addEventListener("error", () => {
  clearTimeout(timeout);
  console.error("CDP websocket error");
  process.exit(1);
});

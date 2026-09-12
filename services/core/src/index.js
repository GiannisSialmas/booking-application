import http from "node:http";

const port = process.env.PORT || 3000;

http
  .createServer((_req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Hello, world");
  })
  .listen(port, () => {
    console.log(`core listening on port ${port}`);
  });

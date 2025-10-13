const fetch = global.fetch || require("node-fetch");

async function demo() {
  console.log("Stateful (server stores):");
  console.log(
    await (await fetch("http://localhost:3000/stateful/alice")).json()
  );
  console.log(
    await (await fetch("http://localhost:3000/stateful/alice")).json()
  );

  console.log("Stateless (client sends state):");
  let counter = 0;
  for (let i = 0; i < 3; i++) {
    const r = await (
      await fetch("http://localhost:3000/stateless", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ counter }),
      })
    ).json();
    console.log(r);
    counter = r.serverCount; // client keeps the state
  }
}

demo().catch(console.error);

package main

import (
	server "github.com/belalakhter/projects/dex_screen/internals/server"
	token "github.com/belalakhter/projects/dex_screen/internals/token"
)

func main() {
	http_eth_client := token.NewEthClient()
	ws_eth_client := token.NewEthClientWS()
	NewServer := server.NewServer(http_eth_client, ws_eth_client)
	NewServer.Start(":8080")
}

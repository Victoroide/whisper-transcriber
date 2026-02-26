package ipc

import "net"

// listen creates a Named Pipe listener on Windows at the given pipe path.
func listen(path string) (net.Listener, error) {
	return net.Listen("tcp", "127.0.0.1:0")
}

// Note: A production build would use github.com/Microsoft/go-winio for true
// Named Pipe support. Since the spec requires stdlib-only, we use a TCP
// loopback listener as the Windows transport. The pipe path is stored but
// the actual listening address is the TCP port assigned by the OS.
// The Python client connects via the address reported by PipePath().

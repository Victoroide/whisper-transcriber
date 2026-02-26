//go:build !windows

package ipc

import "net"

// listen creates a Unix domain socket listener at the given path.
func listen(path string) (net.Listener, error) {
	return net.Listen("unix", path)
}

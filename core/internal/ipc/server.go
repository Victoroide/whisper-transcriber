package ipc

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"path/filepath"
	"runtime"
	"sync"
)

// Server manages the IPC connection between Go core and the Python UI process.
// On Windows it uses a Named Pipe; on Unix systems it uses a Unix domain socket.
type Server struct {
	listener net.Listener
	conn     net.Conn
	mu       sync.Mutex
	done     chan struct{}
	handler  MessageHandler
	pipePath string
}

// MessageHandler processes an incoming message from the Python client and
// returns an optional response message. Return nil to send no response.
type MessageHandler func(msgType string, data json.RawMessage) *Message

// NewServer creates an IPC server using the appropriate transport for the OS.
func NewServer(handler MessageHandler) (*Server, error) {
	pipePath := socketPath()
	if err := cleanStaleSocket(pipePath); err != nil {
		return nil, fmt.Errorf("cleaning stale socket: %w", err)
	}

	listener, err := listen(pipePath)
	if err != nil {
		return nil, fmt.Errorf("creating listener on %s: %w", pipePath, err)
	}

	return &Server{
		listener: listener,
		done:     make(chan struct{}),
		handler:  handler,
		pipePath: listener.Addr().String(),
	}, nil
}

// PipePath returns the address the server is listening on.
// On Windows this is a TCP loopback address; on Unix it is a socket path.
func (s *Server) PipePath() string {
	return s.pipePath
}

// Accept waits for exactly one client connection.
func (s *Server) Accept() error {
	conn, err := s.listener.Accept()
	if err != nil {
		select {
		case <-s.done:
			return nil
		default:
			return fmt.Errorf("accepting connection: %w", err)
		}
	}
	s.mu.Lock()
	s.conn = conn
	s.mu.Unlock()
	return nil
}

// Send writes a JSON message followed by a newline to the connected client.
func (s *Server) Send(msg Message) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.conn == nil {
		return fmt.Errorf("no active connection")
	}
	data, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("marshaling message: %w", err)
	}
	data = append(data, '\n')

	// Create a buffered writer and explicitly flush to avoid batching
	writer := bufio.NewWriter(s.conn)
	if _, err := writer.Write(data); err != nil {
		return fmt.Errorf("writing message: %w", err)
	}
	if err := writer.Flush(); err != nil {
		return fmt.Errorf("flushing message: %w", err)
	}
	return nil
}

// Listen reads newline-delimited JSON messages from the client in a loop,
// dispatching each to the configured handler. Blocks until the connection
// closes or Shutdown is called.
func (s *Server) Listen() error {
	s.mu.Lock()
	conn := s.conn
	s.mu.Unlock()
	if conn == nil {
		return fmt.Errorf("no active connection")
	}

	scanner := bufio.NewScanner(conn)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)

	for scanner.Scan() {
		select {
		case <-s.done:
			return nil
		default:
		}

		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}

		var raw struct {
			Type string          `json:"type"`
			Data json.RawMessage `json:"data"`
		}
		if err := json.Unmarshal(line, &raw); err != nil {
			log.Printf("ipc: failed to parse message: %v", err)
			continue
		}

		if s.handler == nil {
			continue
		}

		resp := s.handler(raw.Type, raw.Data)
		if resp != nil {
			if err := s.Send(*resp); err != nil {
				log.Printf("ipc: failed to send response: %v", err)
			}
		}
	}

	if err := scanner.Err(); err != nil {
		select {
		case <-s.done:
			return nil
		default:
			if err == io.EOF || isClosedError(err) {
				return nil
			}
			return fmt.Errorf("reading from connection: %w", err)
		}
	}
	return nil
}

// Shutdown gracefully closes the server and cleans up resources.
func (s *Server) Shutdown() {
	close(s.done)

	s.mu.Lock()
	if s.conn != nil {
		s.conn.Close()
	}
	s.mu.Unlock()

	s.listener.Close()
	cleanStaleSocket(s.pipePath)
}

// socketPath returns the platform-appropriate IPC endpoint.
func socketPath() string {
	if runtime.GOOS == "windows" {
		return `\\.\pipe\whisper-transcriber-ipc`
	}
	return filepath.Join(os.TempDir(), "whisper-transcriber.sock")
}

// cleanStaleSocket removes a leftover socket file from a previous run.
// On Windows named pipes are managed by the kernel so this is a no-op.
func cleanStaleSocket(path string) error {
	if runtime.GOOS == "windows" {
		return nil
	}
	if _, err := os.Stat(path); err == nil {
		if err := os.Remove(path); err != nil {
			return fmt.Errorf("removing stale socket %s: %w", path, err)
		}
	}
	return nil
}

// isClosedError checks if an error indicates a closed connection.
func isClosedError(err error) bool {
	if err == nil {
		return false
	}
	return err.Error() == "use of closed network connection"
}

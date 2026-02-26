package ipc

import (
	"encoding/json"
	"net"
	"testing"
	"time"
)

func TestServerRoundTrip(t *testing.T) {
	received := make(chan string, 1)

	handler := func(msgType string, data json.RawMessage) *Message {
		received <- msgType
		return &Message{
			Type: "response",
			Data: map[string]string{"status": "ok"},
		}
	}

	srv, err := NewServer(handler)
	if err != nil {
		t.Fatalf("failed to create server: %v", err)
	}
	defer srv.Shutdown()

	// Connect a client in a goroutine
	go func() {
		if err := srv.Accept(); err != nil {
			t.Logf("accept error: %v", err)
			return
		}
		srv.Listen()
	}()

	// Small delay to let the server start accepting
	time.Sleep(50 * time.Millisecond)

	addr := srv.PipePath()
	var conn net.Conn

	// Determine the correct network type based on address format
	if len(addr) > 0 && addr[0] == '/' {
		conn, err = net.Dial("unix", addr)
	} else {
		// On Windows the "pipe path" is actually a TCP address
		conn, err = net.Dial("tcp", addr)
	}
	if err != nil {
		t.Fatalf("failed to connect to server: %v", err)
	}
	defer conn.Close()

	// Send a test message
	msg := `{"type":"test_ping","data":{}}` + "\n"
	if _, err := conn.Write([]byte(msg)); err != nil {
		t.Fatalf("failed to send message: %v", err)
	}

	// Wait for the handler to process the message
	select {
	case msgType := <-received:
		if msgType != "test_ping" {
			t.Fatalf("expected message type 'test_ping', got '%s'", msgType)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for message")
	}

	// Read the response
	buf := make([]byte, 1024)
	conn.SetReadDeadline(time.Now().Add(2 * time.Second))
	n, err := conn.Read(buf)
	if err != nil {
		t.Fatalf("failed to read response: %v", err)
	}

	var resp struct {
		Type string                 `json:"type"`
		Data map[string]interface{} `json:"data"`
	}
	if err := json.Unmarshal(buf[:n-1], &resp); err != nil {
		t.Fatalf("failed to parse response: %v (%s)", err, string(buf[:n]))
	}

	if resp.Type != "response" {
		t.Fatalf("expected response type 'response', got '%s'", resp.Type)
	}
}

func TestServerSendWithoutConnection(t *testing.T) {
	srv, err := NewServer(nil)
	if err != nil {
		t.Fatalf("failed to create server: %v", err)
	}
	defer srv.Shutdown()

	err = srv.Send(Message{Type: "test", Data: nil})
	if err == nil {
		t.Fatal("expected error when sending without connection")
	}
}

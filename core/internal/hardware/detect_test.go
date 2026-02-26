package hardware

import (
	"testing"
)

func TestDetect(t *testing.T) {
	info := Detect()

	if info.CPUCores <= 0 {
		t.Errorf("expected positive CPU core count, got %d", info.CPUCores)
	}

	// RAM detection may return 0 on some CI environments, but should
	// generally be positive on real hardware.
	if info.RAMGB < 0 {
		t.Errorf("expected non-negative RAM, got %d GB", info.RAMGB)
	}

	if info.RecommendedModel == "" {
		t.Error("recommended model should not be empty")
	}

	if info.RecommendedComp == "" {
		t.Error("recommended compute type should not be empty")
	}

	validModels := map[string]bool{
		"tiny": true, "base": true, "small": true,
		"medium": true, "large-v3": true,
	}
	if !validModels[info.RecommendedModel] {
		t.Errorf("unexpected recommended model: %s", info.RecommendedModel)
	}

	validCompute := map[string]bool{"int8": true, "float16": true}
	if !validCompute[info.RecommendedComp] {
		t.Errorf("unexpected recommended compute type: %s", info.RecommendedComp)
	}

	t.Logf("detected: %s", info.String())
}

func TestRecommendCPUOnly(t *testing.T) {
	tests := []struct {
		ramGB         int
		expectedModel string
		expectedComp  string
	}{
		{2, "tiny", "int8"},
		{4, "small", "int8"},
		{8, "medium", "int8"},
		{16, "medium", "int8"},
	}

	for _, tc := range tests {
		info := Info{RAMGB: tc.ramGB, CPUCores: 4}
		model, compute := recommend(info)
		if model != tc.expectedModel {
			t.Errorf("RAM=%dGB: expected model %s, got %s",
				tc.ramGB, tc.expectedModel, model)
		}
		if compute != tc.expectedComp {
			t.Errorf("RAM=%dGB: expected compute %s, got %s",
				tc.ramGB, tc.expectedComp, compute)
		}
	}
}

func TestRecommendWithCUDA(t *testing.T) {
	info := Info{CUDA: true, RAMGB: 16, CPUCores: 8}
	model, compute := recommend(info)
	if model != "large-v3" {
		t.Errorf("expected large-v3 with CUDA and 16GB, got %s", model)
	}
	if compute != "float16" {
		t.Errorf("expected float16 with CUDA, got %s", compute)
	}
}

func TestRecommendWithMPS(t *testing.T) {
	info := Info{MPS: true, RAMGB: 16, CPUCores: 10}
	model, compute := recommend(info)
	if model != "medium" {
		t.Errorf("expected medium with MPS, got %s", model)
	}
	if compute != "float16" {
		t.Errorf("expected float16 with MPS, got %s", compute)
	}
}

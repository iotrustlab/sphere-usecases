// +build ignore

// validate_contract.go validates the tag_contract.yaml file.
// Run with: go run validate_contract.go
package main

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

type TagContract struct {
	APIVersion string   `yaml:"api_version"`
	Kind       string   `yaml:"kind"`
	Metadata   Metadata `yaml:"metadata"`
	Tags       []Tag    `yaml:"tags"`
}

type Metadata struct {
	Name    string `yaml:"name"`
	Version string `yaml:"version"`
}

type Tag struct {
	Name        string    `yaml:"name"`
	Type        string    `yaml:"type"`
	Direction   string    `yaml:"direction"`
	Role        string    `yaml:"role"`
	Group       string    `yaml:"group"`
	Units       string    `yaml:"units,omitempty"`
	Range       []float64 `yaml:"range,omitempty"`
	Description string    `yaml:"description"`
}

func main() {
	data, err := os.ReadFile("tag_contract.yaml")
	if err != nil {
		fmt.Fprintf(os.Stderr, "FAIL: cannot read tag_contract.yaml: %v\n", err)
		os.Exit(1)
	}

	var contract TagContract
	if err := yaml.Unmarshal(data, &contract); err != nil {
		fmt.Fprintf(os.Stderr, "FAIL: invalid YAML: %v\n", err)
		os.Exit(1)
	}

	errors := 0

	// Check required metadata
	if contract.Kind != "TagContract" {
		fmt.Println("FAIL: kind must be 'TagContract'")
		errors++
	}
	if contract.Metadata.Name == "" {
		fmt.Println("FAIL: metadata.name is required")
		errors++
	}

	// Check for duplicates
	seen := make(map[string]bool)
	for _, tag := range contract.Tags {
		if seen[tag.Name] {
			fmt.Printf("FAIL: duplicate tag name: %s\n", tag.Name)
			errors++
		}
		seen[tag.Name] = true
	}

	// Validate each tag
	validTypes := map[string]bool{"bool": true, "real": true, "int": true}
	validDirections := map[string]bool{"sensor": true, "actuator": true}
	validRoles := map[string]bool{"controller": true, "simulator": true, "both": true}

	for _, tag := range contract.Tags {
		if tag.Name == "" {
			fmt.Println("FAIL: tag with empty name")
			errors++
			continue
		}
		if !validTypes[tag.Type] {
			fmt.Printf("FAIL: tag %s has invalid type '%s'\n", tag.Name, tag.Type)
			errors++
		}
		if !validDirections[tag.Direction] {
			fmt.Printf("FAIL: tag %s has invalid direction '%s'\n", tag.Name, tag.Direction)
			errors++
		}
		if !validRoles[tag.Role] {
			fmt.Printf("FAIL: tag %s has invalid role '%s'\n", tag.Name, tag.Role)
			errors++
		}
		if tag.Description == "" {
			fmt.Printf("WARN: tag %s has no description\n", tag.Name)
		}
	}

	fmt.Printf("\nValidated %d tags, %d errors\n", len(contract.Tags), errors)
	if errors > 0 {
		os.Exit(1)
	}
	fmt.Println("PASS: tag contract is valid")
}

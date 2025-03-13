#!/bin/bash
# Script to check container runtime environment

set -e

# Detect container runtimes
DOCKER_PATH=$(which docker 2>/dev/null || echo "")
PODMAN_PATH=$(which podman 2>/dev/null || echo "")
BUILDX_AVAILABLE=0
PODMAN_BUILDX_AVAILABLE=0

echo "Container Runtime Environment Check"
echo "=================================="
echo ""

# Check Docker
if [ -n "$DOCKER_PATH" ]; then
    DOCKER_VERSION=$($DOCKER_PATH --version 2>/dev/null | head -n 1)
    echo "Docker: $DOCKER_VERSION"
    echo "  Path: $DOCKER_PATH"
    
    # Check Docker buildx
    if $DOCKER_PATH buildx version >/dev/null 2>&1; then
        BUILDX_VERSION=$($DOCKER_PATH buildx version 2>/dev/null | head -n 1)
        echo "  Buildx: $BUILDX_VERSION"
        BUILDX_AVAILABLE=1
    else
        echo "  Buildx: Not available"
    fi
    
    # Check Docker Compose
    if $DOCKER_PATH compose version >/dev/null 2>&1; then
        COMPOSE_VERSION=$($DOCKER_PATH compose version 2>/dev/null | head -n 1)
        echo "  Compose: $COMPOSE_VERSION"
    else
        echo "  Compose: Not available"
    fi
else
    echo "Docker: Not installed"
fi

echo ""

# Check Podman
if [ -n "$PODMAN_PATH" ]; then
    PODMAN_VERSION=$($PODMAN_PATH --version 2>/dev/null | head -n 1)
    echo "Podman: $PODMAN_VERSION"
    echo "  Path: $PODMAN_PATH"
    
    # Check Podman buildx compatibility
    if $PODMAN_PATH buildx version >/dev/null 2>&1; then
        PODMAN_BUILDX_VERSION=$($PODMAN_PATH buildx version 2>/dev/null | head -n 1)
        echo "  Buildx compatibility: $PODMAN_BUILDX_VERSION"
        PODMAN_BUILDX_AVAILABLE=1
    else
        echo "  Buildx compatibility: Not available"
    fi
    
    # Check Podman Compose
    if $PODMAN_PATH compose version >/dev/null 2>&1; then
        PODMAN_COMPOSE_VERSION=$($PODMAN_PATH compose version 2>/dev/null | head -n 1)
        echo "  Compose: $PODMAN_COMPOSE_VERSION"
    else
        echo "  Compose: Not available"
    fi
else
    echo "Podman: Not installed"
fi

echo ""

# Determine recommended runtime
if [ -n "$DOCKER_PATH" ] && [ -n "$PODMAN_PATH" ]; then
    echo "Both Docker and Podman are available."
    if [ "$BUILDX_AVAILABLE" -eq 1 ] && [ "$PODMAN_BUILDX_AVAILABLE" -eq 0 ]; then
        echo "Recommendation: Use Docker for multi-architecture builds (buildx available)"
        echo "  make FORCE_DOCKER=1 <target>"
    elif [ "$PODMAN_BUILDX_AVAILABLE" -eq 1 ] && [ "$BUILDX_AVAILABLE" -eq 0 ]; then
        echo "Recommendation: Use Podman for multi-architecture builds (buildx available)"
        echo "  make FORCE_PODMAN=1 <target>"
    else
        echo "Recommendation: Either runtime is suitable for your needs"
    fi
elif [ -n "$DOCKER_PATH" ]; then
    echo "Only Docker is available."
    echo "Recommendation: Use Docker"
    echo "  make FORCE_DOCKER=1 <target>"
elif [ -n "$PODMAN_PATH" ]; then
    echo "Only Podman is available."
    echo "Recommendation: Use Podman"
    echo "  make FORCE_PODMAN=1 <target>"
else
    echo "No container runtime found."
    echo "Recommendation: Install Docker or Podman"
fi

echo ""
echo "For more information, run: make container-info" 
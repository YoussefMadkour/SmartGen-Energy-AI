/**
 * WebSocket Client for Real-Time Telemetry Updates
 * Handles connection management, automatic reconnection, and message parsing
 */

import { config, endpoints } from './config';
import type { TelemetryReading, WebSocketMessage } from '../types';

/**
 * Connection status enum
 */
export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

/**
 * WebSocket client configuration
 */
interface WebSocketConfig {
  maxReconnectAttempts?: number;
  initialReconnectDelay?: number;
  maxReconnectDelay?: number;
  reconnectBackoffMultiplier?: number;
}

/**
 * Callback types
 */
type MessageCallback = (data: TelemetryReading) => void;
type StatusCallback = (status: ConnectionStatus) => void;
type ErrorCallback = (error: Error) => void;

/**
 * TelemetryWebSocket class for managing real-time telemetry data stream
 */
export class TelemetryWebSocket {
  private ws: WebSocket | null = null;
  private status: ConnectionStatus = ConnectionStatus.DISCONNECTED;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private shouldReconnect = true;

  // Configuration
  private readonly maxReconnectAttempts: number;
  private readonly initialReconnectDelay: number;
  private readonly maxReconnectDelay: number;
  private readonly reconnectBackoffMultiplier: number;

  // Callbacks
  private onMessageCallback: MessageCallback | null = null;
  private onStatusChangeCallback: StatusCallback | null = null;
  private onErrorCallback: ErrorCallback | null = null;

  /**
   * Create a new TelemetryWebSocket instance
   */
  constructor(config?: WebSocketConfig) {
    this.maxReconnectAttempts = config?.maxReconnectAttempts ?? 10;
    this.initialReconnectDelay = config?.initialReconnectDelay ?? 1000; // 1 second
    this.maxReconnectDelay = config?.maxReconnectDelay ?? 30000; // 30 seconds
    this.reconnectBackoffMultiplier = config?.reconnectBackoffMultiplier ?? 2;
  }

  /**
   * Connect to the WebSocket server
   * @param onMessage - Callback for receiving telemetry data
   * @param onStatusChange - Optional callback for connection status changes
   * @param onError - Optional callback for errors
   */
  connect(
    onMessage: MessageCallback,
    onStatusChange?: StatusCallback,
    onError?: ErrorCallback
  ): void {
    // Store callbacks
    this.onMessageCallback = onMessage;
    this.onStatusChangeCallback = onStatusChange || null;
    this.onErrorCallback = onError || null;

    // Enable reconnection
    this.shouldReconnect = true;

    // Initiate connection
    this.createConnection();
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    // Disable automatic reconnection
    this.shouldReconnect = false;

    // Clear any pending reconnection attempts
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Close the WebSocket connection
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }

    // Update status
    this.updateStatus(ConnectionStatus.DISCONNECTED);

    // Reset reconnection counter
    this.reconnectAttempts = 0;
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /**
   * Check if currently connected
   */
  isConnected(): boolean {
    return this.status === ConnectionStatus.CONNECTED;
  }

  /**
   * Create WebSocket connection
   */
  private createConnection(): void {
    try {
      // Update status
      const isReconnecting = this.reconnectAttempts > 0;
      this.updateStatus(
        isReconnecting ? ConnectionStatus.RECONNECTING : ConnectionStatus.CONNECTING
      );

      // Build WebSocket URL
      const wsUrl = `${config.wsUrl}${endpoints.websocket.telemetry}`;

      // Create WebSocket instance
      this.ws = new WebSocket(wsUrl);

      // Set up event handlers
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      this.handleConnectionError(
        error instanceof Error ? error : new Error('Failed to create WebSocket')
      );
    }
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    console.log('[WebSocket] Connected to telemetry stream');

    // Reset reconnection counter on successful connection
    this.reconnectAttempts = 0;

    // Update status
    this.updateStatus(ConnectionStatus.CONNECTED);
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      // Parse message
      const message = this.parseMessage(event.data);

      // Validate and handle based on message type
      if (message.type === 'telemetry' && message.data) {
        // Validate telemetry data
        const telemetry = this.validateTelemetryData(message.data);

        // Call the message callback
        if (this.onMessageCallback) {
          this.onMessageCallback(telemetry);
        }
      } else if (message.type === 'error') {
        console.error('[WebSocket] Server error:', message.data);
        this.handleError(new Error(String(message.data)));
      }
    } catch (error) {
      console.error('[WebSocket] Failed to process message:', error);
      this.handleError(
        error instanceof Error ? error : new Error('Message processing failed')
      );
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(event: Event | Error): void {
    const error = event instanceof Error ? event : new Error('WebSocket error');
    console.error('[WebSocket] Error:', error);

    // Update status
    this.updateStatus(ConnectionStatus.ERROR);

    // Call error callback
    if (this.onErrorCallback) {
      this.onErrorCallback(error);
    }
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    console.log(
      `[WebSocket] Connection closed (code: ${event.code}, reason: ${event.reason})`
    );

    // Clear WebSocket instance
    this.ws = null;

    // Update status
    this.updateStatus(ConnectionStatus.DISCONNECTED);

    // Attempt reconnection if enabled and not a normal closure
    if (this.shouldReconnect && event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle connection errors
   */
  private handleConnectionError(error: Error): void {
    console.error('[WebSocket] Connection error:', error);

    // Update status
    this.updateStatus(ConnectionStatus.ERROR);

    // Call error callback
    if (this.onErrorCallback) {
      this.onErrorCallback(error);
    }

    // Attempt reconnection if enabled
    if (this.shouldReconnect) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt with exponential backoff
   */
  private scheduleReconnect(): void {
    // Check if max attempts reached
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(
        `[WebSocket] Max reconnection attempts (${this.maxReconnectAttempts}) reached`
      );
      this.updateStatus(ConnectionStatus.ERROR);
      return;
    }

    // Calculate delay with exponential backoff
    const delay = Math.min(
      this.initialReconnectDelay *
        Math.pow(this.reconnectBackoffMultiplier, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    this.reconnectAttempts++;

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    // Schedule reconnection
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.createConnection();
    }, delay);
  }

  /**
   * Parse WebSocket message
   */
  private parseMessage(data: string): WebSocketMessage {
    try {
      const parsed = JSON.parse(data);

      // Validate message structure
      if (!parsed || typeof parsed !== 'object') {
        throw new Error('Invalid message format');
      }

      if (!parsed.type) {
        throw new Error('Message missing type field');
      }

      return parsed as WebSocketMessage;
    } catch (error) {
      throw new Error(
        `Failed to parse message: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Validate telemetry data structure
   */
  private validateTelemetryData(data: unknown): TelemetryReading {
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid telemetry data: not an object');
    }

    const telemetry = data as Partial<TelemetryReading>;

    // Validate required fields
    if (!telemetry.timestamp) {
      throw new Error('Invalid telemetry data: missing timestamp');
    }

    if (typeof telemetry.power_load_kw !== 'number') {
      throw new Error('Invalid telemetry data: invalid power_load_kw');
    }

    if (typeof telemetry.fuel_consumption_lph !== 'number') {
      throw new Error('Invalid telemetry data: invalid fuel_consumption_lph');
    }

    if (!telemetry.status || !['ON', 'OFF'].includes(telemetry.status)) {
      throw new Error('Invalid telemetry data: invalid status');
    }

    return telemetry as TelemetryReading;
  }

  /**
   * Update connection status and notify callback
   */
  private updateStatus(newStatus: ConnectionStatus): void {
    if (this.status !== newStatus) {
      this.status = newStatus;

      // Call status change callback
      if (this.onStatusChangeCallback) {
        this.onStatusChangeCallback(newStatus);
      }
    }
  }
}

/**
 * Create a singleton instance for convenience
 */
export const telemetryWebSocket = new TelemetryWebSocket();


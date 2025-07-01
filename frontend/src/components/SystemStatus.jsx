import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Server, 
  Database, 
  Brain, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  RefreshCw,
  Clock,
  Cpu,
  HardDrive,
  Wifi
} from 'lucide-react';

function SystemStatus() {
  const [systemStatus, setSystemStatus] = useState({
    lastUpdated: new Date(),
    services: {
      backend: { status: 'healthy', responseTime: 45, lastCheck: new Date() },
      llm: { status: 'healthy', responseTime: 1200, lastCheck: new Date(), model: 'mistral' },
      rag: { status: 'healthy', responseTime: 300, lastCheck: new Date(), documents: 150 },
      database: { status: 'healthy', responseTime: 25, lastCheck: new Date(), connections: 5 }
    },
    metrics: {
      uptime: '2d 14h 32m',
      totalRequests: 1247,
      avgResponseTime: 430,
      errorRate: 0.02,
      memoryUsage: 68,
      cpuUsage: 23,
      diskUsage: 45
    }
  });
  
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refreshStatus = async () => {
    setIsRefreshing(true);
    
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/status');
      if (response.ok) {
        const data = await response.json();
        setSystemStatus(prev => ({
          ...data,
          lastUpdated: new Date()
        }));
      } else {
        // Simulate status for demo
        setSystemStatus(prev => ({
          ...prev,
          lastUpdated: new Date(),
          services: {
            ...prev.services,
            backend: { ...prev.services.backend, lastCheck: new Date() },
            llm: { ...prev.services.llm, lastCheck: new Date() },
            rag: { ...prev.services.rag, lastCheck: new Date() },
            database: { ...prev.services.database, lastCheck: new Date() }
          }
        }));
      }
    } catch (error) {
      console.error('Failed to refresh status:', error);
    } finally {
      setTimeout(() => setIsRefreshing(false), 1000);
    }
  };

  useEffect(() => {
    // Auto-refresh every 30 seconds
    const interval = setInterval(refreshStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle size={20} style={{ color: 'var(--karray-success)' }} />;
      case 'warning':
        return <AlertTriangle size={20} style={{ color: 'var(--karray-warning)' }} />;
      case 'error':
        return <XCircle size={20} style={{ color: 'var(--karray-error)' }} />;
      default:
        return <Activity size={20} style={{ color: 'var(--karray-text-secondary)' }} />;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'healthy':
        return 'status-success';
      case 'warning':
        return 'status-warning';
      case 'error':
        return 'status-error';
      default:
        return '';
    }
  };

  const formatResponseTime = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatLastCheck = (date) => {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  };

  const getUsageColor = (percentage) => {
    if (percentage < 50) return 'var(--karray-success)';
    if (percentage < 80) return 'var(--karray-warning)';
    return 'var(--karray-error)';
  };

  return (
    <div className="container" style={{ maxWidth: '1000px', padding: 'var(--space-4)' }}>
      {/* Header */}
      <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-8)' }}>
        <div>
          <h1>System Status</h1>
          <p style={{ color: 'var(--karray-text-secondary)' }}>
            Real-time monitoring of K-Array Chat system components
          </p>
        </div>
        
        <button
          onClick={refreshStatus}
          className="btn btn-secondary"
          disabled={isRefreshing}
        >
          <RefreshCw size={16} className={isRefreshing ? 'loading' : ''} />
          Refresh
        </button>
      </div>

      {/* Overall Status */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-4)' }}>
          <h2 style={{ margin: 0 }}>Overall Health</h2>
          <div className="flex items-center gap-2">
            <CheckCircle size={20} style={{ color: 'var(--karray-success)' }} />
            <span className="status-indicator status-success">All Systems Operational</span>
          </div>
        </div>
        
        <div style={{ 
          fontSize: 'var(--font-size-sm)',
          color: 'var(--karray-text-secondary)'
        }}>
          Last updated: {systemStatus.lastUpdated.toLocaleString()}
        </div>
      </div>

      {/* Services Status */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <h2 style={{ marginBottom: 'var(--space-4)' }}>Services</h2>
        
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 'var(--space-4)'
        }}>
          {/* Backend Service */}
          <div style={{
            padding: 'var(--space-4)',
            border: '1px solid var(--karray-border)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--karray-surface)'
          }}>
            <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-3)' }}>
              <Server size={24} style={{ color: 'var(--karray-primary)' }} />
              <div>
                <h3 style={{ margin: 0 }}>Backend API</h3>
                <div className="flex items-center gap-2">
                  {getStatusIcon(systemStatus.services.backend.status)}
                  <span className={`status-indicator ${getStatusClass(systemStatus.services.backend.status)}`}>
                    {systemStatus.services.backend.status}
                  </span>
                </div>
              </div>
            </div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--karray-text-secondary)' }}>
              <div>Response: {formatResponseTime(systemStatus.services.backend.responseTime)}</div>
              <div>Last check: {formatLastCheck(systemStatus.services.backend.lastCheck)}</div>
            </div>
          </div>

          {/* LLM Service */}
          <div style={{
            padding: 'var(--space-4)',
            border: '1px solid var(--karray-border)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--karray-surface)'
          }}>
            <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-3)' }}>
              <Brain size={24} style={{ color: 'var(--karray-primary)' }} />
              <div>
                <h3 style={{ margin: 0 }}>LLM Engine</h3>
                <div className="flex items-center gap-2">
                  {getStatusIcon(systemStatus.services.llm.status)}
                  <span className={`status-indicator ${getStatusClass(systemStatus.services.llm.status)}`}>
                    {systemStatus.services.llm.status}
                  </span>
                </div>
              </div>
            </div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--karray-text-secondary)' }}>
              <div>Model: {systemStatus.services.llm.model}</div>
              <div>Response: {formatResponseTime(systemStatus.services.llm.responseTime)}</div>
              <div>Last check: {formatLastCheck(systemStatus.services.llm.lastCheck)}</div>
            </div>
          </div>

          {/* RAG Service */}
          <div style={{
            padding: 'var(--space-4)',
            border: '1px solid var(--karray-border)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--karray-surface)'
          }}>
            <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-3)' }}>
              <Database size={24} style={{ color: 'var(--karray-primary)' }} />
              <div>
                <h3 style={{ margin: 0 }}>RAG System</h3>
                <div className="flex items-center gap-2">
                  {getStatusIcon(systemStatus.services.rag.status)}
                  <span className={`status-indicator ${getStatusClass(systemStatus.services.rag.status)}`}>
                    {systemStatus.services.rag.status}
                  </span>
                </div>
              </div>
            </div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--karray-text-secondary)' }}>
              <div>Documents: {systemStatus.services.rag.documents?.toLocaleString()}</div>
              <div>Response: {formatResponseTime(systemStatus.services.rag.responseTime)}</div>
              <div>Last check: {formatLastCheck(systemStatus.services.rag.lastCheck)}</div>
            </div>
          </div>

          {/* Database Service */}
          <div style={{
            padding: 'var(--space-4)',
            border: '1px solid var(--karray-border)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--karray-surface)'
          }}>
            <div className="flex items-center gap-3" style={{ marginBottom: 'var(--space-3)' }}>
              <Database size={24} style={{ color: 'var(--karray-primary)' }} />
              <div>
                <h3 style={{ margin: 0 }}>Vector Database</h3>
                <div className="flex items-center gap-2">
                  {getStatusIcon(systemStatus.services.database.status)}
                  <span className={`status-indicator ${getStatusClass(systemStatus.services.database.status)}`}>
                    {systemStatus.services.database.status}
                  </span>
                </div>
              </div>
            </div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--karray-text-secondary)' }}>
              <div>Connections: {systemStatus.services.database.connections}</div>
              <div>Response: {formatResponseTime(systemStatus.services.database.responseTime)}</div>
              <div>Last check: {formatLastCheck(systemStatus.services.database.lastCheck)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* System Metrics */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <h2 style={{ marginBottom: 'var(--space-4)' }}>System Metrics</h2>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: 'var(--space-4)'
        }}>
          {/* Uptime */}
          <div className="flex items-center gap-3">
            <Clock size={20} style={{ color: 'var(--karray-primary)' }} />
            <div>
              <div style={{ fontWeight: '500' }}>Uptime</div>
              <div style={{ fontSize: 'var(--font-size-lg)', color: 'var(--karray-success)' }}>
                {systemStatus.metrics.uptime}
              </div>
            </div>
          </div>

          {/* Total Requests */}
          <div className="flex items-center gap-3">
            <Wifi size={20} style={{ color: 'var(--karray-primary)' }} />
            <div>
              <div style={{ fontWeight: '500' }}>Total Requests</div>
              <div style={{ fontSize: 'var(--font-size-lg)', color: 'var(--karray-primary)' }}>
                {systemStatus.metrics.totalRequests?.toLocaleString()}
              </div>
            </div>
          </div>

          {/* Average Response Time */}
          <div className="flex items-center gap-3">
            <Activity size={20} style={{ color: 'var(--karray-primary)' }} />
            <div>
              <div style={{ fontWeight: '500' }}>Avg Response</div>
              <div style={{ fontSize: 'var(--font-size-lg)', color: 'var(--karray-primary)' }}>
                {formatResponseTime(systemStatus.metrics.avgResponseTime)}
              </div>
            </div>
          </div>

          {/* Error Rate */}
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} style={{ color: 'var(--karray-primary)' }} />
            <div>
              <div style={{ fontWeight: '500' }}>Error Rate</div>
              <div style={{ 
                fontSize: 'var(--font-size-lg)', 
                color: systemStatus.metrics.errorRate > 0.05 ? 'var(--karray-error)' : 'var(--karray-success)'
              }}>
                {(systemStatus.metrics.errorRate * 100).toFixed(2)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Resource Usage */}
      <div className="card">
        <h2 style={{ marginBottom: 'var(--space-4)' }}>Resource Usage</h2>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 'var(--space-6)'
        }}>
          {/* Memory Usage */}
          <div>
            <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-3)' }}>
              <Cpu size={20} style={{ color: 'var(--karray-primary)' }} />
              <span style={{ fontWeight: '500' }}>Memory Usage</span>
              <span style={{ 
                marginLeft: 'auto',
                fontSize: 'var(--font-size-lg)',
                color: getUsageColor(systemStatus.metrics.memoryUsage)
              }}>
                {systemStatus.metrics.memoryUsage}%
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              backgroundColor: 'var(--karray-border)',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${systemStatus.metrics.memoryUsage}%`,
                height: '100%',
                backgroundColor: getUsageColor(systemStatus.metrics.memoryUsage),
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>

          {/* CPU Usage */}
          <div>
            <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-3)' }}>
              <Cpu size={20} style={{ color: 'var(--karray-primary)' }} />
              <span style={{ fontWeight: '500' }}>CPU Usage</span>
              <span style={{ 
                marginLeft: 'auto',
                fontSize: 'var(--font-size-lg)',
                color: getUsageColor(systemStatus.metrics.cpuUsage)
              }}>
                {systemStatus.metrics.cpuUsage}%
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              backgroundColor: 'var(--karray-border)',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${systemStatus.metrics.cpuUsage}%`,
                height: '100%',
                backgroundColor: getUsageColor(systemStatus.metrics.cpuUsage),
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>

          {/* Disk Usage */}
          <div>
            <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-3)' }}>
              <HardDrive size={20} style={{ color: 'var(--karray-primary)' }} />
              <span style={{ fontWeight: '500' }}>Disk Usage</span>
              <span style={{ 
                marginLeft: 'auto',
                fontSize: 'var(--font-size-lg)',
                color: getUsageColor(systemStatus.metrics.diskUsage)
              }}>
                {systemStatus.metrics.diskUsage}%
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              backgroundColor: 'var(--karray-border)',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${systemStatus.metrics.diskUsage}%`,
                height: '100%',
                backgroundColor: getUsageColor(systemStatus.metrics.diskUsage),
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SystemStatus;
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MessageCircle, Upload, Activity, Menu } from 'lucide-react';

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Chat', href: '/', icon: MessageCircle },
    { name: 'Upload', href: '/upload', icon: Upload },
    { name: 'Status', href: '/status', icon: Activity },
  ];

  const isActive = (path) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <div className="layout">
      {/* Header */}
      <header className="header">
        <div className="container flex items-center justify-between" style={{ padding: 'var(--space-4)' }}>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="btn btn-secondary"
              style={{ padding: 'var(--space-2)' }}
            >
              <Menu size={20} />
            </button>
            <Link to="/" className="flex items-center gap-4" style={{ textDecoration: 'none' }}>
              <div style={{
                width: '32px',
                height: '32px',
                backgroundColor: 'var(--karray-primary)',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold'
              }}>
                K
              </div>
              <h1 style={{ margin: 0, fontSize: 'var(--font-size-xl)', color: 'var(--karray-primary)' }}>
                K-Array Chat
              </h1>
            </Link>
          </div>
          
          <nav className="flex gap-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`btn ${isActive(item.href) ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ textDecoration: 'none' }}
                >
                  <Icon size={16} />
                  <span style={{ display: window.innerWidth > 768 ? 'inline' : 'none' }}>
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Sidebar for mobile */}
      {sidebarOpen && (
        <div
          style={{
            position: 'fixed',
            top: '0',
            left: '0',
            right: '0',
            bottom: '0',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: '200',
            display: window.innerWidth > 768 ? 'none' : 'block'
          }}
          onClick={() => setSidebarOpen(false)}
        >
          <div
            style={{
              position: 'fixed',
              top: '0',
              left: '0',
              width: '250px',
              height: '100vh',
              backgroundColor: 'var(--karray-background)',
              boxShadow: 'var(--shadow-lg)',
              padding: 'var(--space-6)',
              transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
              transition: 'transform 0.3s ease-in-out'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ marginBottom: 'var(--space-8)' }}>
              <h2 style={{ fontSize: 'var(--font-size-lg)', margin: 0 }}>Navigation</h2>
            </div>
            
            <nav className="flex flex-col gap-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`btn w-full ${isActive(item.href) ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ 
                      textDecoration: 'none',
                      justifyContent: 'flex-start'
                    }}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon size={16} />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="main-content">
        {children}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--karray-border)',
        backgroundColor: 'var(--karray-surface)',
        padding: 'var(--space-4) 0',
        marginTop: 'auto'
      }}>
        <div className="container text-center">
          <p style={{
            margin: 0,
            fontSize: 'var(--font-size-sm)',
            color: 'var(--karray-text-secondary)'
          }}>
            Powered by <strong>K-Array</strong> AI Technology - 
            <a 
              href="https://www.k-array.com" 
              target="_blank" 
              rel="noopener noreferrer"
              style={{
                color: 'var(--karray-primary)',
                textDecoration: 'none',
                marginLeft: 'var(--space-1)'
              }}
            >
              www.k-array.com
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  MessageSquare, 
  Sparkles, 
  Upload, 
  Activity, 
  TestTube,
  Menu,
  X,
  ChevronRight,
  Bot,
  Settings,
  HelpCircle
} from 'lucide-react';

const gradients = {
  primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  karray: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)'
};

const navigationItems = [
  {
    path: '/chat/modern',
    label: 'Chat Moderno',
    icon: Sparkles,
    description: 'Interfaccia moderna con animazioni fluide',
    gradient: gradients.primary,
    isNew: true
  },
  {
    path: '/chat/streaming',
    label: 'Chat Streaming',
    icon: MessageSquare,
    description: 'Interfaccia con streaming in tempo reale',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  },
  {
    path: '/chat/legacy',
    label: 'Chat Classico',
    icon: Bot,
    description: 'Interfaccia tradizionale semplice',
    gradient: gradients.karray
  },
  {
    path: '/upload',
    label: 'Upload Documenti',
    icon: Upload,
    description: 'Carica documenti nel sistema',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    path: '/status',
    label: 'Stato Sistema',
    icon: Activity,
    description: 'Monitora lo stato del sistema',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  },
  {
    path: '/test',
    label: 'Test',
    icon: TestTube,
    description: 'Area di test e sviluppo',
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
  }
];

function NavigationItem({ item, isActive, isMobile = false }) {
  const [isHovered, setIsHovered] = useState(false);

  const itemStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: isMobile ? '12px' : '16px',
    padding: isMobile ? '12px 16px' : '16px 20px',
    borderRadius: '12px',
    textDecoration: 'none',
    color: isActive ? 'white' : '#64748b',
    background: isActive ? item.gradient : isHovered ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
    border: isActive ? 'none' : '1px solid rgba(255, 255, 255, 0.1)',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative',
    overflow: 'hidden',
    backdropFilter: isHovered ? 'blur(10px)' : 'none',
    transform: isHovered && !isMobile ? 'translateX(8px)' : 'translateX(0)',
    boxShadow: isActive ? '0 8px 24px rgba(0, 0, 0, 0.15)' : isHovered ? '0 4px 12px rgba(0, 0, 0, 0.1)' : 'none'
  };

  const iconStyle = {
    flexShrink: 0,
    opacity: isActive ? 1 : 0.7,
    transition: 'all 0.3s ease'
  };

  const textStyle = {
    flex: 1,
    fontSize: isMobile ? '14px' : '15px',
    fontWeight: isActive ? '600' : '500',
    transition: 'all 0.3s ease'
  };

  return (
    <Link
      to={item.path}
      style={itemStyle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Glass morphism effect */}
      {(isActive || isHovered) && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: isActive ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(10px)',
          borderRadius: '12px',
          pointerEvents: 'none'
        }} />
      )}

      <item.icon size={isMobile ? 18 : 20} style={iconStyle} />
      
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={textStyle}>{item.label}</div>
        {!isMobile && (
          <div style={{
            fontSize: '12px',
            opacity: isActive ? 0.9 : 0.6,
            lineHeight: 1.3,
            marginTop: '2px'
          }}>
            {item.description}
          </div>
        )}
      </div>

      {item.isNew && (
        <div style={{
          padding: '2px 8px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #ff6b6b 0%, #ffd93d 100%)',
          color: 'white',
          fontSize: '10px',
          fontWeight: '700',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          position: 'relative',
          zIndex: 1
        }}>
          NEW
        </div>
      )}

      {!isMobile && (
        <ChevronRight 
          size={16} 
          style={{ 
            opacity: isHovered ? 1 : 0,
            transform: isHovered ? 'translateX(0)' : 'translateX(-4px)',
            transition: 'all 0.3s ease',
            position: 'relative',
            zIndex: 1
          }} 
        />
      )}
    </Link>
  );
}

function MobileMenu({ isOpen, onClose }) {
  const location = useLocation();

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      backdropFilter: 'blur(10px)',
      zIndex: 1000,
      animation: 'fadeIn 0.3s ease-out'
    }}>
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '280px',
        height: '100%',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '24px',
        animation: 'slideInLeft 0.3s ease-out'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '32px'
        }}>
          <h2 style={{
            color: 'white',
            fontSize: '20px',
            fontWeight: '700',
            margin: 0
          }}>
            K-Array AI
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: 'none',
              borderRadius: '8px',
              padding: '8px',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {navigationItems.map((item) => (
            <NavigationItem
              key={item.path}
              item={item}
              isActive={location.pathname === item.path}
              isMobile={true}
            />
          ))}
        </div>

        <div style={{
          position: 'absolute',
          bottom: '24px',
          left: '24px',
          right: '24px'
        }}>
          <div style={{
            padding: '16px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              <HelpCircle size={16} color="white" />
              <span style={{ color: 'white', fontSize: '14px', fontWeight: '600' }}>
                Aiuto
              </span>
            </div>
            <p style={{
              color: 'rgba(255, 255, 255, 0.8)',
              fontSize: '12px',
              margin: 0,
              lineHeight: 1.4
            }}>
              Hai domande? Usa l'interfaccia chat per assistenza immediata.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ModernNavigation() {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Desktop Navigation */}
      <nav style={{
        display: 'none',
        position: 'fixed',
        top: '24px',
        left: '24px',
        width: '320px',
        height: 'calc(100vh - 48px)',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        padding: '24px',
        zIndex: 100,
        flexDirection: 'column',
        '@media (min-width: 1024px)': {
          display: 'flex'
        }
      }}>
        {/* Header */}
        <div style={{
          marginBottom: '32px',
          textAlign: 'center'
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            margin: '0 auto 16px',
            borderRadius: '16px',
            background: gradients.karray,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)'
          }}>
            <Bot size={32} color="white" />
          </div>
          <h1 style={{
            fontSize: '24px',
            fontWeight: '700',
            margin: '0 0 8px',
            background: gradients.karray,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            K-Array AI
          </h1>
          <p style={{
            fontSize: '14px',
            color: '#64748b',
            margin: 0,
            lineHeight: 1.4
          }}>
            Sistema di assistenza intelligente per prodotti e servizi K-Array
          </p>
        </div>

        {/* Navigation Items */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {navigationItems.map((item) => (
            <NavigationItem
              key={item.path}
              item={item}
              isActive={location.pathname === item.path}
            />
          ))}
        </div>

        {/* Footer */}
        <div style={{
          padding: '20px',
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
          borderRadius: '12px',
          border: '1px solid rgba(102, 126, 234, 0.2)',
          marginTop: '24px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '8px'
          }}>
            <Settings size={16} color="#4f46e5" />
            <span style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#4f46e5'
            }}>
              Stato Sistema
            </span>
          </div>
          <p style={{
            fontSize: '12px',
            color: '#64748b',
            margin: 0,
            lineHeight: 1.4
          }}>
            RAG System: ✅ Operativo<br />
            K-Framework: ✅ Connesso<br />
            Confidence: 0.8/1.0
          </p>
        </div>
      </nav>

      {/* Mobile Navigation Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 20px',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        '@media (min-width: 1024px)': {
          display: 'none'
        }
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: gradients.karray,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Bot size={20} color="white" />
          </div>
          <div>
            <h1 style={{
              fontSize: '18px',
              fontWeight: '700',
              margin: 0,
              color: '#1a1a1a'
            }}>
              K-Array AI
            </h1>
          </div>
        </div>

        <button
          onClick={() => setIsMobileMenuOpen(true)}
          style={{
            background: 'rgba(102, 126, 234, 0.1)',
            border: 'none',
            borderRadius: '8px',
            padding: '8px',
            color: '#4f46e5',
            cursor: 'pointer'
          }}
        >
          <Menu size={20} />
        </button>
      </div>

      {/* Mobile Menu */}
      <MobileMenu 
        isOpen={isMobileMenuOpen} 
        onClose={() => setIsMobileMenuOpen(false)} 
      />

      <style jsx>{`
        @media (min-width: 1024px) {
          nav {
            display: flex !important;
          }
          .mobile-header {
            display: none !important;
          }
        }
      `}</style>
    </>
  );
}
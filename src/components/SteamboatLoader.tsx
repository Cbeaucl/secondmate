import React from 'react';
import styles from './SteamboatLoader.module.css';

export const SteamboatLoader: React.FC = () => {
    return (
        <div className={styles.container}>
            <div className={styles.scene}>
                <svg viewBox="-20 -20 280 280" className={styles.spinner} fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="wood" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#6B4226" />
                            <stop offset="50%" stopColor="#8A5A33" />
                            <stop offset="100%" stopColor="#4A2B14" />
                        </linearGradient>
                        <linearGradient id="woodLight" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#8A5A33" />
                            <stop offset="50%" stopColor="#A86F3F" />
                            <stop offset="100%" stopColor="#6B4226" />
                        </linearGradient>
                        <linearGradient id="brass" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#FFF2B2" />
                            <stop offset="25%" stopColor="#D4AF37" />
                            <stop offset="75%" stopColor="#AA842C" />
                            <stop offset="100%" stopColor="#5C4010" />
                        </linearGradient>
                        <radialGradient id="hubBrass" cx="30%" cy="30%" r="70%">
                            <stop offset="0%" stopColor="#FFF2B2" />
                            <stop offset="30%" stopColor="#D4AF37" />
                            <stop offset="80%" stopColor="#AA842C" />
                            <stop offset="100%" stopColor="#5C4010" />
                        </radialGradient>
                        <filter id="rim-shadow" x="-30%" y="-30%" width="160%" height="160%">
                            <feDropShadow dx="0" dy="6" stdDeviation="5" floodColor="#000" floodOpacity="0.35" />
                        </filter>
                        <filter id="drop-shadow" x="-30%" y="-30%" width="160%" height="160%">
                            <feDropShadow dx="0" dy="12" stdDeviation="15" floodColor="#000" floodOpacity="0.25" />
                        </filter>

                        <g id="spoke">
                            {/* Inner Spoke */}
                            <path d="M 116 96 L 117 55 L 123 55 L 124 96 Z" fill="url(#wood)" />
                            <path d="M 117 96 L 117.5 55 L 120 55 L 120 96 Z" fill="url(#woodLight)" />

                            {/* Handle */}
                            <path d="M 115 30 L 116.5 22 C 116.5 18 117.5 16 117.5 13 L 122.5 13 C 122.5 16 123.5 18 123.5 22 L 125 30 Z" fill="url(#wood)" />
                            <path d="M 116 30 L 117 22 C 117 18 118 16 118 13 L 120 13 C 120 16 120 18 120 30 Z" fill="url(#woodLight)" />

                            {/* Knob */}
                            <circle cx="120" cy="10" r="6" fill="url(#wood)" filter="url(#rim-shadow)" />
                            <circle cx="118.5" cy="9" r="2.5" fill="url(#woodLight)" />

                            {/* Brass Ring */}
                            <rect x="114" y="27" width="12" height="3" fill="url(#brass)" />
                        </g>

                        <g id="rim-plate">
                            <path d="M 115.5 55 L 124.5 55 L 122.5 30 L 117.5 30 Z" fill="url(#brass)" />
                            <circle cx="120" cy="50" r="1.5" fill="#5C4010" />
                            <circle cx="120" cy="35" r="1.5" fill="#5C4010" />
                        </g>
                    </defs>

                    <g filter="url(#drop-shadow)">
                        {/* Spokes */}
                        {[0, 45, 90, 135, 180, 225, 270, 315].map(angle => (
                            <use href="#spoke" transform={`rotate(${angle} 120 120)`} key={`spoke-${angle}`} />
                        ))}

                        {/* Outer Wheel Rim */}
                        <circle cx="120" cy="120" r="77.5" fill="none" stroke="url(#wood)" strokeWidth="25" filter="url(#rim-shadow)" />
                        <circle cx="120" cy="120" r="77.5" fill="none" stroke="url(#woodLight)" strokeWidth="23" opacity="0.4" />

                        {/* Trim lines */}
                        <circle cx="120" cy="120" r="90" fill="none" stroke="#2D1A0C" strokeWidth="1" />
                        <circle cx="120" cy="120" r="65" fill="none" stroke="#2D1A0C" strokeWidth="1" />

                        {/* Brass Inlay */}
                        <circle cx="120" cy="120" r="77.5" fill="none" stroke="url(#brass)" strokeWidth="5" />
                        <circle cx="120" cy="120" r="77.5" fill="none" stroke="#8C6914" strokeWidth="1" />

                        {/* Rim Plates */}
                        {[0, 45, 90, 135, 180, 225, 270, 315].map(angle => (
                            <use href="#rim-plate" transform={`rotate(${angle} 120 120)`} key={`plate-${angle}`} />
                        ))}

                        {/* Center Hub */}
                        <circle cx="120" cy="120" r="28" fill="#2D1A0C" filter="url(#rim-shadow)" />
                        <circle cx="120" cy="120" r="26" fill="url(#hubBrass)" />
                        <circle cx="120" cy="120" r="18" fill="none" stroke="#AA842C" strokeWidth="1.5" />

                        {/* Inner wood center */}
                        <circle cx="120" cy="120" r="13" fill="url(#wood)" />

                        {/* Compass Star in hub */}
                        <path d="M 120 109 L 122.5 117.5 L 131 120 L 122.5 122.5 L 120 131 L 117.5 122.5 L 109 120 L 117.5 117.5 Z" fill="url(#brass)" />
                        <circle cx="120" cy="120" r="2.5" fill="#FFE55C" />
                    </g>
                </svg>
            </div>
            <div className={styles.text}>
                CHARTING COURSE...
            </div>
        </div>
    );
};

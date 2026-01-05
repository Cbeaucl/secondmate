import React from 'react';
import styles from './SteamboatLoader.module.css';

export const SteamboatLoader: React.FC = () => {
    return (
        <div className={styles.container}>
            <div className={styles.scene}>
                <div className={styles.boatContainer}>
                    {/* SVG Steamboat - Responsive */}
                    <svg width="100%" height="100%" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ overflow: 'visible' }}>
                        {/* Hull */}
                        <path d="M10 60 L30 90 H90 L110 60 Z" fill="#8B4513" stroke="#5D4037" strokeWidth="2" />
                        {/* Cabin */}
                        <rect x="35" y="30" width="50" height="30" fill="#F5F5DC" stroke="#8B4513" strokeWidth="2" />
                        <rect x="40" y="35" width="10" height="10" fill="#87CEEB" />
                        <rect x="55" y="35" width="10" height="10" fill="#87CEEB" />
                        <rect x="70" y="35" width="10" height="10" fill="#87CEEB" />
                        {/* Roof */}
                        <path d="M30 30 H90" stroke="#8B4513" strokeWidth="4" />
                        {/* Smokestack */}
                        <rect x="60" y="10" width="10" height="20" fill="#333" />
                        <rect x="58" y="8" width="14" height="4" fill="#000" />
                        {/* Paddlewheel */}
                        <circle cx="20" cy="75" r="12" fill="#A0522D" stroke="#5D4037" strokeWidth="2" />
                        <path d="M10 75 H30 M20 65 V85" stroke="#5D4037" strokeWidth="2" />
                    </svg>

                    {/* Smoke puffs */}
                    <div className={styles.smoke}></div>
                    <div className={styles.smoke}></div>
                    <div className={styles.smoke}></div>
                </div>

                <div className={styles.river}>
                    <div className={styles.wave}></div>
                    <div className={styles.wave}></div>
                    <div className={styles.wave}></div>
                    <div className={styles.wave}></div>
                    <div className={styles.wave}></div>
                </div>
            </div>
            <div className={styles.text}>
                Steaming down line...
            </div>
        </div>
    );
};

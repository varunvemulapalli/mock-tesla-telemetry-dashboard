import React, { useState } from 'react';
import { Device } from '../../types/device';
import { healthApi } from '../../services/api';
import './HealthAnalysis.css';

interface HealthAnalysisProps {
  device: Device;
}

const HealthAnalysis: React.FC<HealthAnalysisProps> = ({ device }) => {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [analysisType, setAnalysisType] = useState<'comprehensive' | 'battery' | 'solar' | 'grid'>('comprehensive');

  const runAnalysis = async () => {
    try {
      setLoading(true);
      const result = await healthApi.analyze(device.device_id, analysisType, true);
      setAnalysis(result);
    } catch (error: any) {
      console.error('Error running health analysis:', error);
      setAnalysis({
        overall_health_score: 0,
        analysis: 'Error: Could not complete health analysis. Please try again.',
        recommendations: [],
        key_metrics: {},
      });
    } finally {
      setLoading(false);
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'high';
    if (score >= 60) return 'medium';
    return 'low';
  };

  return (
    <div className="health-analysis">
      <div className="card">
        <h2>AI-Powered Health Analysis</h2>
        <p className="analysis-description">
          Get intelligent insights about your {device.model} system health, performance, and optimization opportunities.
        </p>

        <div className="analysis-controls">
          <div className="analysis-type-selector">
            <label>Analysis Type:</label>
            <select
              className="select"
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value as any)}
              disabled={loading}
            >
              <option value="comprehensive">Comprehensive</option>
              <option value="battery">Battery Health</option>
              <option value="solar">Solar Performance</option>
              <option value="grid">Grid Interaction</option>
            </select>
          </div>
          <button
            className="button"
            onClick={runAnalysis}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Run Health Analysis'}
          </button>
        </div>
      </div>

      {analysis && (
        <>
          <div className="card">
            <h2>Health Score</h2>
            <div className="health-score-display">
              <div className={`health-score-circle ${getHealthScoreColor(analysis.overall_health_score)}`}>
                <div className="health-score-value">
                  {analysis.overall_health_score.toFixed(0)}
                </div>
                <div className="health-score-label">Health Score</div>
              </div>
              <div className="health-score-description">
                {analysis.overall_health_score >= 80 && (
                  <p>Your system is operating at optimal levels. Continue monitoring for best performance.</p>
                )}
                {analysis.overall_health_score >= 60 && analysis.overall_health_score < 80 && (
                  <p>Your system is functioning well but could benefit from optimization. Review recommendations below.</p>
                )}
                {analysis.overall_health_score < 60 && (
                  <p>Your system may require attention. Please review the analysis and recommendations carefully.</p>
                )}
              </div>
            </div>
          </div>

          <div className="card">
            <h2>Analysis Report</h2>
            <div className="analysis-text">
              {analysis.analysis.split('\n').map((paragraph: string, index: number) => (
                <p key={index}>{paragraph}</p>
              ))}
            </div>
          </div>

          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <div className="card">
              <h2>Recommendations</h2>
              <ul className="recommendations-list">
                {analysis.recommendations.map((rec: string, index: number) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {analysis.key_metrics && Object.keys(analysis.key_metrics).length > 0 && (
            <div className="card">
              <h2>Key Metrics</h2>
              <div className="metrics-grid">
                {Object.entries(analysis.key_metrics).map(([key, value]) => (
                  <div key={key} className="metric-item">
                    <div className="metric-label">{key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}</div>
                    <div className="metric-value">
                      {typeof value === 'number' ? value.toFixed(2) : String(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card">
            <div className="analysis-timestamp">
              Analysis generated: {new Date(analysis.timestamp).toLocaleString()}
            </div>
          </div>
        </>
      )}

      {!analysis && !loading && (
        <div className="no-analysis">
          <p>Click "Run Health Analysis" to get AI-powered insights about your system.</p>
        </div>
      )}
    </div>
  );
};

export default HealthAnalysis;


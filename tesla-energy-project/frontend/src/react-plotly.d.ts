// Type declarations for react-plotly.js
declare module 'react-plotly.js' {
  import { Component } from 'react';
  import { Data, Layout, Config } from 'plotly.js';

  interface PlotParams {
    data: Data[];
    layout?: Partial<Layout>;
    config?: Partial<Config>;
    frames?: any[];
    revision?: number;
    onInitialized?: (figure: any, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: any, graphDiv: HTMLElement) => void;
    onPurge?: (figure: any, graphDiv: HTMLElement) => void;
    onError?: (err: any) => void;
    debug?: boolean;
    useResizeHandler?: boolean;
    style?: React.CSSProperties;
    className?: string;
    onRelayout?: (eventData: any) => void;
    onRedraw?: () => void;
    onBeforePlot?: (eventData: any) => boolean | void;
    onAfterPlot?: () => void;
    onAnimatingFrame?: (eventData: any) => void;
    onAnimationInterrupted?: () => void;
    onDeselect?: () => void;
    onDoubleClick?: () => void;
    onHover?: (eventData: any) => void;
    onUnhover?: () => void;
    onSelected?: (eventData: any) => void;
    onSelecting?: (eventData: any) => void;
    onSunburstClick?: (eventData: any) => void;
    onTransitioning?: () => void;
    onTransitionInterrupted?: () => void;
    onLegendClick?: (eventData: any) => boolean;
    onLegendDoubleClick?: (eventData: any) => boolean;
    onSliderChange?: (eventData: any) => void;
    onSliderEnd?: (eventData: any) => void;
    onSliderStart?: (eventData: any) => void;
    divId?: string;
  }

  export default class Plot extends Component<PlotParams> {}
}


"use client"

import React, { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi } from 'lightweight-charts'

interface SignalChartProps {
  symbol: string
  entry?: number
  sl?: number
  tp?: number
}

const SignalChart: React.FC<SignalChartProps> = ({ symbol, entry, sl, tp }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const [chartError, setChartError] = useState(false)

  useEffect(() => {
    if (!chartContainerRef.current) return

    const container = chartContainerRef.current;
    let chart: IChartApi | null = null;

    try {
        chart = createChart(container, {
          layout: {
            background: { type: ColorType.Solid, color: 'transparent' },
            textColor: '#94a3b8',
          },
          grid: {
            vertLines: { color: '#1e293b' },
            horzLines: { color: '#1e293b' },
          },
          width: container.clientWidth,
          height: 200,
          timeScale: {
            borderColor: '#1e293b',
          },
        })

        if (!chart || typeof (chart as any).addCandlestickSeries !== 'function') {
            throw new Error("Chart initialization failed");
        }

        const candlestickSeries = (chart as any).addCandlestickSeries({
          upColor: '#10b981',
          downColor: '#ef4444',
          borderVisible: false,
          wickUpColor: '#10b981',
          wickDownColor: '#ef4444',
        })

        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://quant-2.onrender.com/api/v1';

        fetch(`${API_URL}/history/ohlcv?symbol=${symbol}`)
          .then(res => res.json())
          .then(data => {
            if (data && Array.isArray(data) && candlestickSeries) {
                candlestickSeries.setData(data)
                
                if (entry) candlestickSeries.createPriceLine({ price: entry, color: '#3b82f6', lineWidth: 2, title: 'ENTRY' })
                if (sl) candlestickSeries.createPriceLine({ price: sl, color: '#ef4444', lineWidth: 2, title: 'SL' })
                if (tp) candlestickSeries.createPriceLine({ price: tp, color: '#10b981', lineWidth: 2, title: 'TP' })

                chart?.timeScale().fitContent()
            }
          })
          .catch(err => console.warn("Chart data fetch failed:", err))

        const handleResize = () => {
          chart?.applyOptions({ width: container.clientWidth })
        }

        window.addEventListener('resize', handleResize)

        return () => {
          window.removeEventListener('resize', handleResize)
          chart?.remove()
        }
    } catch (err) {
        console.error("Critical Chart Error:", err)
        setChartError(true)
        return () => {}
    }
  }, [symbol, entry, sl, tp])

  if (chartError) {
    return (
        <div className="w-full h-[200px] bg-slate-900/50 rounded-xl flex items-center justify-center border border-slate-800">
            <span className="text-xs text-slate-500 italic">Chart visualization temporarily unavailable</span>
        </div>
    )
  }

  return <div ref={chartContainerRef} className="w-full" />
}

export default SignalChart

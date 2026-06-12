import { cn } from '../../lib/utils'

import type { HTMLAttributes } from 'react'

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
  variant?: 'pulse' | 'shimmer'
}

export function Skeleton({ className, variant = 'pulse', ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded-md bg-muted',
        variant === 'pulse' && 'animate-pulse',
        variant === 'shimmer' && 'animate-shimmer',
        className
      )}
      {...props}
    />
  )
}

interface SkeletonCardProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
  rows?: number
}

export function SkeletonCard({ className, rows = 3, ...props }: SkeletonCardProps) {
  return (
    <div className={cn('rounded-xl border border-border bg-card p-4 space-y-3', className)} {...props}>
      <Skeleton className="h-5 w-1/3" />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  )
}

interface SkeletonTableProps {
  rows?: number
  cols?: number
}

export function SkeletonTable({ rows = 5, cols = 4 }: SkeletonTableProps) {
  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={`h-${i}`} className="h-8 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-2">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={`${r}-${c}`} className="h-10 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

interface SkeletonShimmerProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
}

export function SkeletonShimmerCard({ className, ...props }: SkeletonShimmerProps) {
  return (
    <div className={cn('rounded-xl border border-border bg-card p-4', className)} {...props}>
      <div className="flex items-center gap-3 mb-3">
        <Skeleton variant="shimmer" className="w-10 h-10 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="shimmer" className="h-3 rounded w-24" />
          <Skeleton variant="shimmer" className="h-2 rounded w-16" />
        </div>
      </div>
      <div className="space-y-2 mb-3">
        <Skeleton variant="shimmer" className="h-4 rounded w-full" />
        <Skeleton variant="shimmer" className="h-4 rounded w-3/4" />
      </div>
      <Skeleton variant="shimmer" className="h-24 rounded-lg mb-3" />
      <div className="flex gap-2">
        <Skeleton variant="shimmer" className="h-8 rounded-lg flex-1" />
        <Skeleton variant="shimmer" className="h-8 rounded-lg w-16" />
      </div>
    </div>
  )
}

interface SkeletonShimmerListProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
  items?: number
}

export function SkeletonShimmerList({ className, items = 4, ...props }: SkeletonShimmerListProps) {
  return (
    <div className={cn('rounded-xl border border-border bg-card p-4', className)} {...props}>
      <Skeleton variant="shimmer" className="h-4 rounded w-20 mb-3" />
      <div className="space-y-3">
        {Array.from({ length: items }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton variant="shimmer" className="w-8 h-8 rounded-lg" />
            <div className="flex-1 space-y-1.5">
              <Skeleton variant="shimmer" className="h-3 rounded w-full" />
              <Skeleton variant="shimmer" className="h-2 rounded w-2/3" />
            </div>
            <Skeleton variant="shimmer" className="h-3 rounded w-12" />
          </div>
        ))}
      </div>
    </div>
  )
}

interface SkeletonShimmerBentoProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
}

export function SkeletonShimmerBento({ className, ...props }: SkeletonShimmerBentoProps) {
  return (
    <div className={cn('rounded-xl border border-border bg-card p-4', className)} {...props}>
      <Skeleton variant="shimmer" className="h-4 rounded w-32 mb-3" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Skeleton variant="shimmer" className="aspect-square rounded-xl" />
        <Skeleton variant="shimmer" className="aspect-square rounded-xl" />
        <Skeleton variant="shimmer" className="col-span-2 aspect-[2/1] rounded-xl" />
        <Skeleton variant="shimmer" className="col-span-2 row-span-2 rounded-xl" />
        <Skeleton variant="shimmer" className="aspect-square rounded-xl" />
        <Skeleton variant="shimmer" className="aspect-square rounded-xl" />
        <Skeleton variant="shimmer" className="col-span-2 aspect-[2/1] rounded-xl" />
      </div>
    </div>
  )
}

import React from 'react';

/** Shared TonerTrack mark - SVG app icon + wordmark */
const BrandMark: React.FC<{
  size?: number;
  showWordmark?: boolean;
  className?: string;
  wordmarkClassName?: string;
}> = ({
  size = 32,
  showWordmark = true,
  className = '',
  wordmarkClassName = 'tt-display text-lg tracking-wide',
}) => (
  <span className={`inline-flex items-center gap-2.5 min-w-0 ${className}`}>
    <img
      src={`${process.env.PUBLIC_URL || ''}/logo.svg`}
      alt=""
      width={size}
      height={size}
      className="rounded-md shrink-0"
      decoding="async"
    />
    {showWordmark && (
      <span className={`truncate ${wordmarkClassName}`}>TonerTrack</span>
    )}
  </span>
);

export default BrandMark;

import React from 'react';

/** Network-wide scan disabled in Step 1 trust model. */
const ScanButton: React.FC = () => {
  return (
    <button
      type="button"
      disabled
      title="Subnet scan is disabled. Add printers one by one."
      className="opacity-50 cursor-not-allowed px-3 py-2 rounded-lg border text-sm"
    >
      Scan disabled
    </button>
  );
};

export default ScanButton;

import React from "react";
import "./ProgressBar.sass";

interface Props {
  progress: number;
  progressMessage: string;
}

const ProgressBar = ({ progress, progressMessage }: Props) => {
  console.log(progress);
  const style = {
    width: progress + "%",
    transition: `width 200ms`,
  };
  return (
    <div className="ProgressBar">
      <div className="message">{progressMessage}</div>
      <div className="progress-bar">
        <div className="progress" style={style} />
      </div>
    </div>
  );
};

export default ProgressBar;

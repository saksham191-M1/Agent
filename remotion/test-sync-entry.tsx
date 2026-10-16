import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { AudioSyncTest } from './AudioSyncTest';

const testPayload = {
  test_id: "audio_sync_001",
  fps: 30,
  scene: {
    component_id: "TestButton",
    trigger_frame: 45
  },
  audio_cue: {
    sync_to_component: "TestButton",
    file_path: "test_pop.wav" 
  }
};

export const Root: React.FC = () => {
  return (
    <Composition
      id="AudioSyncTest"
      component={AudioSyncTest}
      durationInFrames={90}
      fps={testPayload.fps}
      width={1920}
      height={1080}
      defaultProps={{
        sceneData: testPayload.scene,
        audioData: testPayload.audio_cue,
      }}
    />
  );
};

registerRoot(Root);

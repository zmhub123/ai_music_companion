import { useState } from 'react'
import { Button, Modal, Radio, Space, Typography } from 'antd'
import { useScoreStore, type ScoreInstrument } from '../../stores/scoreStore'
import type { VocalVersion } from '../../types/score'

interface FormProps {
  defaultInstrument: ScoreInstrument
  defaultVocal: VocalVersion
  onCancel: () => void
  onConfirm: (instrument: ScoreInstrument, vocalVersion: VocalVersion) => void
}

function ScoreGenerateForm({
  defaultInstrument,
  defaultVocal,
  onCancel,
  onConfirm,
}: FormProps) {
  const [instrument, setInstrument] = useState(defaultInstrument)
  const [vocalVersion, setVocalVersion] = useState(defaultVocal)

  return (
    <>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 20 }}>
        选择乐器与演唱版本，系统将分析音频并生成弹唱谱
      </Typography.Paragraph>
      <div className="score-generate-form">
        <div className="score-generate-field">
          <div className="score-generate-label">乐器</div>
          <Radio.Group
            value={instrument}
            onChange={(e) => setInstrument(e.target.value as ScoreInstrument)}
            optionType="button"
            buttonStyle="solid"
            className="score-generate-radio"
          >
            <Radio.Button value="guitar">吉他</Radio.Button>
            <Radio.Button value="ukulele">尤克里里</Radio.Button>
          </Radio.Group>
        </div>
        <div className="score-generate-field">
          <div className="score-generate-label">音色版本</div>
          <Radio.Group
            value={vocalVersion}
            onChange={(e) => setVocalVersion(e.target.value as VocalVersion)}
            optionType="button"
            buttonStyle="solid"
            className="score-generate-radio"
          >
            <Radio.Button value="male">男声版</Radio.Button>
            <Radio.Button value="female">女声版</Radio.Button>
          </Radio.Group>
        </div>
      </div>
      <Space style={{ width: '100%', justifyContent: 'flex-end', marginTop: 28 }}>
        <Button onClick={onCancel}>取消</Button>
        <Button type="primary" onClick={() => onConfirm(instrument, vocalVersion)}>
          进入曲谱
        </Button>
      </Space>
    </>
  )
}

export default function ScoreGenerateModal() {
  const modalOpen = useScoreStore((s) => s.modalOpen)
  const storeInstrument = useScoreStore((s) => s.instrument)
  const storeVocal = useScoreStore((s) => s.vocalVersion)
  const closeGenerateModal = useScoreStore((s) => s.closeGenerateModal)
  const confirmGenerate = useScoreStore((s) => s.confirmGenerate)

  return (
    <Modal
      title="生成曲谱"
      open={modalOpen}
      onCancel={closeGenerateModal}
      footer={null}
      centered
      destroyOnHidden
      width={420}
    >
      {modalOpen ? (
        <ScoreGenerateForm
          key={`${storeInstrument}-${storeVocal}`}
          defaultInstrument={storeInstrument}
          defaultVocal={storeVocal}
          onCancel={closeGenerateModal}
          onConfirm={confirmGenerate}
        />
      ) : null}
    </Modal>
  )
}

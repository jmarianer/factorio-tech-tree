import { useParams } from 'react-router-dom';
import { Dialog } from './Dialog';
import { useData } from './DataContext';
import BBCodeComponent from '@bbob/react';
import { createPreset } from '@bbob/preset';

const factorioPreset = createPreset({
  font: (node) => (
     {
      tag: 'b',
      content: node.content,
    }),
  color: (node) => ({
      tag: 'span',
      attrs: {
        style: {
          color: Object.keys(node.attrs || {})[0],
        },
      },
      content: node.content,
    }),
  br: () => ({ tag: 'br' }),
})

function BBCode(props: { code: string }) {
  return <BBCodeComponent plugins={[factorioPreset()]}>{props.code.replaceAll('\\n', '[br]')}</BBCodeComponent>;
}


export default function Item() {
  const { regime, type, name } = useParams();
  const data = useData();
  const item = data.items[name!];

  return Dialog(`Item: ${item.localized_title('en')}`,
    <>
      <img src={`/generated/${regime}/icons/${type}/${name}.png`} alt={name} />
      <div className="description">
        <BBCode code={item.description('en')} />
      </div>
    </>,
    <div>
    </div>
  );
}

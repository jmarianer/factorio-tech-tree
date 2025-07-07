import { useParams } from "react-router-dom";
import { useData } from "./DataContext";
import { BBCode } from "./BBCode";
import { Dialog } from "./Dialog";
import { CraftingMachine as CraftingMachineType, Turret as TurretType, Lab as LabType } from "./FactorioTypes";
import { ItemIcon, RenderRecipe } from "./Elements";

function CraftingMachine({ entity }: { entity: CraftingMachineType }) {
  const data = useData();
  const { regime } = useParams();
  return <>
    <img src={`/generated/${regime}/animations/${entity.type}/${entity.name}.webp`} alt={entity.name} /><br />
    Crafting speed: {entity.crafting_speed} <br />
    <h2>Crafting</h2>
    {entity.crafting_categories.map((category) => (
      <div key={category}>
        <h3>{category}</h3>
        <div className="recipe-list">
          {Object.values(data.recipes).filter((recipe) => recipe.crafting_category === category).map((recipe) => (
            <RenderRecipe key={recipe.name} recipe={recipe} />
          ))}
        </div>
      </div>
    ))}
  </>;
} 

function Lab({ entity }: { entity: LabType }) {
  const data = useData();
  const { regime } = useParams();
  return <>
    <img src={`/generated/${regime}/animations/${entity.type}/${entity.name}.webp`} alt={entity.name} /><br />
    Research speed: {entity.researching_speed} <br />
    Inputs: {entity.inputs.map((input) => (
      <ItemIcon key={input} item={data.items[input]} />
    ))} <br />
  </>;
} 

function Turret({ entity }: { entity: TurretType }) {
  // TODO deuglify
  const attackParams = entity.json['attack_parameters'];
  return <>
    {attackParams.type} turret. <br />
    Range:
    {attackParams.min_range && `${attackParams.min_range} – `}
    {attackParams.range} <br />
    {entity.ammo_categories && (
      <>
        Ammo categories: <br />
        {entity.ammo_categories.map(([category, ammo]) => (
          <div key={category}>
            {category}
            {Array.isArray(ammo) && ammo.map((item) => (
              <ItemIcon key={item.name} item={item} />
            ))}
          </div>
        ))}
      </>
    )}
  </>;
}

export default function Entity() {
  const { regime, name } = useParams();
  const data = useData();
  const entity = data.entities[name!];
  return Dialog(`Entity: ${entity.name}`,
    <>
      <img src={`/generated/${regime}/icons/${entity.type}/${entity.name}.png`} alt={entity.name} />
      <div className="description">
        <BBCode code={entity.description('en')} />
      </div>
    </>,
    entity instanceof CraftingMachineType ? <CraftingMachine entity={entity} /> :
    entity instanceof LabType ? <Lab entity={entity} /> :
    entity instanceof TurretType ? <Turret entity={entity} /> : null
  );
}
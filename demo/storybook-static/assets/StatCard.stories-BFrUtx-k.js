import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{C as N}from"./Card-DwETJY6u.js";import{c}from"./utils-DaT-yT0k.js";import{c as i}from"./createLucideIcon-C15OmZG9.js";import"./index-DzGJhHoF.js";const q={default:"text-muted-foreground",primary:"text-primary",success:"text-emerald-600",warning:"text-amber-600",danger:"text-red-600"};function a({label:k,value:S,icon:j,variant:w="default",className:T}){return e.jsxs(N,{className:c("p-4 text-center",T),children:[e.jsx(j,{className:c("w-5 h-5 mx-auto mb-2",q[w])}),e.jsx("div",{className:"text-2xl font-bold text-foreground tracking-tight",children:S}),e.jsx("div",{className:"text-xs text-muted-foreground mt-1",children:k})]})}a.__docgenInfo={description:"",methods:[],displayName:"StatCard",props:{label:{required:!0,tsType:{name:"string"},description:""},value:{required:!0,tsType:{name:"union",raw:"string | number",elements:[{name:"string"},{name:"number"}]},description:""},icon:{required:!0,tsType:{name:"LucideIcon"},description:""},variant:{required:!1,tsType:{name:"union",raw:"'default' | 'success' | 'warning' | 'danger' | 'primary'",elements:[{name:"literal",value:"'default'"},{name:"literal",value:"'success'"},{name:"literal",value:"'warning'"},{name:"literal",value:"'danger'"},{name:"literal",value:"'primary'"}]},description:"",defaultValue:{value:"'default'",computed:!1}},className:{required:!1,tsType:{name:"string"},description:""}}};/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const b=i("ChartColumn",[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16",key:"c24i48"}],["path",{d:"M18 17V9",key:"2bz60n"}],["path",{d:"M13 17V5",key:"1frdt8"}],["path",{d:"M8 17v-3",key:"17ska0"}]]);/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l=i("CircleCheck",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"m9 12 2 2 4-4",key:"dzmm74"}]]);/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M=i("TrendingUp",[["polyline",{points:"22 7 13.5 15.5 8.5 10.5 2 17",key:"126l90"}],["polyline",{points:"16 7 22 7 22 13",key:"kwv8wd"}]]);/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A=i("TriangleAlert",[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3",key:"wmoenq"}],["path",{d:"M12 9v4",key:"juzpu7"}],["path",{d:"M12 17h.01",key:"p32p05"}]]),B={title:"Common/StatCard",component:a,tags:["autodocs"],argTypes:{variant:{control:"select",options:["default","primary","success","warning","danger"]}}},r={args:{label:"已发布",value:156,icon:b,variant:"default"}},n={args:{label:"覆盖率",value:"83%",icon:l,variant:"success"}},t={args:{label:"待审核",value:8,icon:A,variant:"warning"}},s={render:()=>e.jsxs("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-4",children:[e.jsx(a,{label:"待生成",value:12,icon:b,variant:"primary"}),e.jsx(a,{label:"已发布",value:156,icon:l,variant:"success"}),e.jsx(a,{label:"互动增长",value:"+23%",icon:M,variant:"primary"}),e.jsx(a,{label:"平均健康分",value:87,icon:l,variant:"default"})]})};var o,d,u;r.parameters={...r.parameters,docs:{...(o=r.parameters)==null?void 0:o.docs,source:{originalSource:`{
  args: {
    label: '已发布',
    value: 156,
    icon: BarChart3,
    variant: 'default'
  }
}`,...(u=(d=r.parameters)==null?void 0:d.docs)==null?void 0:u.source}}};var m,p,g;n.parameters={...n.parameters,docs:{...(m=n.parameters)==null?void 0:m.docs,source:{originalSource:`{
  args: {
    label: '覆盖率',
    value: '83%',
    icon: CheckCircle2,
    variant: 'success'
  }
}`,...(g=(p=n.parameters)==null?void 0:p.docs)==null?void 0:g.source}}};var v,y,f;t.parameters={...t.parameters,docs:{...(v=t.parameters)==null?void 0:v.docs,source:{originalSource:`{
  args: {
    label: '待审核',
    value: 8,
    icon: AlertTriangle,
    variant: 'warning'
  }
}`,...(f=(y=t.parameters)==null?void 0:y.docs)==null?void 0:f.source}}};var h,x,C;s.parameters={...s.parameters,docs:{...(h=s.parameters)==null?void 0:h.docs,source:{originalSource:`{
  render: () => <div className="grid grid-cols-2 md:grid-cols-4 gap-4">\r
      <StatCard label="待生成" value={12} icon={BarChart3} variant="primary" />\r
      <StatCard label="已发布" value={156} icon={CheckCircle2} variant="success" />\r
      <StatCard label="互动增长" value="+23%" icon={TrendingUp} variant="primary" />\r
      <StatCard label="平均健康分" value={87} icon={CheckCircle2} variant="default" />\r
    </div>
}`,...(C=(x=s.parameters)==null?void 0:x.docs)==null?void 0:C.source}}};const D=["Default","Success","Warning","Grid"];export{r as Default,s as Grid,n as Success,t as Warning,D as __namedExportsOrder,B as default};

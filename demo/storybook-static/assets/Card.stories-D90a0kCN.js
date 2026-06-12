import{j as r}from"./jsx-runtime-D_zvdyIk.js";import{C as h,a as s,b as u,c as x}from"./Card-DwETJY6u.js";import{B as j}from"./Button-BnaN5BD7.js";import"./utils-DaT-yT0k.js";import"./createLucideIcon-C15OmZG9.js";import"./index-DzGJhHoF.js";const w={title:"UI/Card",component:h,tags:["autodocs"],argTypes:{hover:{control:"boolean"},shadow:{control:"select",options:["none","sm","md"]}}},e={args:{children:r.jsx(s,{children:"这是卡片内容区域"})}},a={render:()=>r.jsxs(h,{children:[r.jsx(u,{children:r.jsx("h3",{className:"text-sm font-semibold",children:"卡片标题"})}),r.jsx(s,{children:"卡片正文内容"}),r.jsx(x,{children:r.jsx(j,{size:"sm",children:"确认"})})]})},o={args:{hover:!0,shadow:"sm",children:r.jsx(s,{children:"悬停查看效果"})}};var t,n,d;e.parameters={...e.parameters,docs:{...(t=e.parameters)==null?void 0:t.docs,source:{originalSource:`{
  args: {
    children: <CardContent>这是卡片内容区域</CardContent>
  }
}`,...(d=(n=e.parameters)==null?void 0:n.docs)==null?void 0:d.source}}};var c,m,i;a.parameters={...a.parameters,docs:{...(c=a.parameters)==null?void 0:c.docs,source:{originalSource:`{
  render: () => <Card>\r
      <CardHeader>\r
        <h3 className="text-sm font-semibold">卡片标题</h3>\r
      </CardHeader>\r
      <CardContent>卡片正文内容</CardContent>\r
      <CardFooter>\r
        <Button size="sm">确认</Button>\r
      </CardFooter>\r
    </Card>
}`,...(i=(m=a.parameters)==null?void 0:m.docs)==null?void 0:i.source}}};var l,C,p;o.parameters={...o.parameters,docs:{...(l=o.parameters)==null?void 0:l.docs,source:{originalSource:`{
  args: {
    hover: true,
    shadow: 'sm',
    children: <CardContent>悬停查看效果</CardContent>
  }
}`,...(p=(C=o.parameters)==null?void 0:C.docs)==null?void 0:p.source}}};const F=["Default","WithHeader","Hoverable"];export{e as Default,o as Hoverable,a as WithHeader,F as __namedExportsOrder,w as default};

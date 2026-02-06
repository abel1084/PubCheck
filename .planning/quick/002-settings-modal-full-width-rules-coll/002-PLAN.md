---
phase: quick
plan: 002
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/components/Settings/Settings.tsx
autonomous: true

must_haves:
  truths:
    - "Custom rule Input and Remove button fill the full width of the Collapse panel"
    - "All settings sections (Cover Page, Typography, Images, Margins, Required Elements, Custom Rules) start collapsed when the modal opens"
  artifacts:
    - path: "frontend/src/components/Settings/Settings.tsx"
      provides: "Settings modal with collapsed sections and full-width custom rules"
  key_links: []
---

<objective>
Fix two UI issues in the Settings modal: (1) make custom rules form fields and button fill the full available width of their container, and (2) start all Collapse accordion sections as collapsed by default.

Purpose: Improve usability of the settings modal -- full-width inputs are easier to type in, and collapsed sections reduce visual noise on open.
Output: Updated Settings.tsx with both fixes applied.
</objective>

<execution_context>
@C:\Users\abelb\.claude/get-shit-done/workflows/execute-plan.md
@C:\Users\abelb\.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@frontend/src/components/Settings/Settings.tsx
</context>

<tasks>

<task type="auto">
  <name>Task 1: Full-width custom rules + collapsed accordions</name>
  <files>frontend/src/components/Settings/Settings.tsx</files>
  <action>
Two targeted changes in Settings.tsx:

**1. Fix CustomRulesForm full-width (lines ~427-452):**

The antd `Space` component wraps each child in a `div` that does not stretch, so `flex: 1` on the Input has no effect. Replace the `Space` wrapper with a plain `div` using flexbox:

```tsx
// Replace <Space key={index} style={{ width: '100%' }}> ... </Space>
// with:
<div key={index} style={{ display: 'flex', gap: 8, width: '100%' }}>
  <Input
    value={rule}
    onChange={e => {
      const newRules = [...rules];
      newRules[index] = e.target.value;
      onChange(newRules);
    }}
    placeholder="e.g., Charts must use UNEP color palette"
    style={{ flex: 1 }}
  />
  <Button danger onClick={() => onChange(rules.filter((_, i) => i !== index))}>
    Remove
  </Button>
</div>
```

This ensures the Input's `flex: 1` actually stretches to fill remaining width after the Remove button.

**2. Collapse all sections by default (line ~206):**

Change the Collapse component from:
```tsx
<Collapse
  defaultActiveKey={['cover', 'typography', 'images', 'margins', 'required']}
  items={collapseItems}
/>
```
to:
```tsx
<Collapse
  items={collapseItems}
/>
```

Remove the `defaultActiveKey` prop entirely so no panels are open by default.
  </action>
  <verify>
Run `npx tsc --noEmit` from the frontend directory to confirm no type errors. Then visually verify:
1. Open the Settings modal -- all six accordion sections should be collapsed
2. Expand "Custom Rules" -- the Input field and Remove button should span the full width of the panel
3. The "+ Add Rule" button should still be full width (it already has `block` prop)
  </verify>
  <done>Custom rules Input+Button fill container width using flex div instead of antd Space. All Collapse sections start collapsed (no defaultActiveKey).</done>
</task>

</tasks>

<verification>
- Open Settings modal: all 6 sections (Cover Page, Typography, Images, Margins, Required Elements, Custom Rules) are collapsed
- Click to expand Custom Rules: add a rule, confirm the input field stretches to fill width with Remove button on the right
- No TypeScript errors from `npx tsc --noEmit`
</verification>

<success_criteria>
- All Collapse accordion sections start collapsed when Settings modal opens
- Custom rules Input and Remove button fill 100% of the available container width
- No regressions in other settings sections
</success_criteria>

<output>
After completion, create `.planning/quick/002-settings-modal-full-width-rules-coll/002-SUMMARY.md`
</output>

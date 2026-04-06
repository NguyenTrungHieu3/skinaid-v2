'use client';

import { useState } from 'react';
import {
  GripVertical,
  Edit2,
  Trash2,
  PlusCircle,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  ChevronDown,
  Plus,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// Type definitions
interface Answer {
  id: string;
  text: string;
  triageLevel: 'light' | 'moderate' | 'severe';
}

interface Question {
  id: string;
  order: number;
  title: string;
  answers: Answer[];
}

interface Questionnaire {
  id: string;
  name: string;
  category: string;
  status: 'active' | 'draft';
  questions: Question[];
}

// Dummy data
const DUMMY_QUESTIONNAIRES: Questionnaire[] = [
  {
    id: '1',
    name: 'Bộ câu hỏi đánh giá Bỏng',
    category: 'Bỏng',
    status: 'active',
    questions: [
      {
        id: 'q1',
        order: 1,
        title: 'Hình dạng và vùng phỏng của vết bỏng?',
        answers: [
          { id: 'a1', text: 'Bỏng nhỏ, diện tích dưới 10cm²', triageLevel: 'light' },
          { id: 'a2', text: 'Bỏng trung bình, diện tích 10-50cm²', triageLevel: 'moderate' },
          { id: 'a3', text: 'Bỏng lớn, diện tích trên 50cm²', triageLevel: 'severe' },
        ],
      },
      {
        id: 'q2',
        order: 2,
        title: 'Vị trí của vết bỏng trên cơ thể?',
        answers: [
          { id: 'a4', text: 'Tay, chân (vùng không nhạy cảm)', triageLevel: 'light' },
          { id: 'a5', text: 'Lưng, ngực', triageLevel: 'moderate' },
          { id: 'a6', text: 'Mặt, cộc tai, bìu', triageLevel: 'severe' },
        ],
      },
    ],
  },
  {
    id: '2',
    name: 'Bộ câu hỏi đánh giá Trầy xước',
    category: 'Trầy xước',
    status: 'draft',
    questions: [],
  },
  {
    id: '3',
    name: 'Bộ câu hỏi đánh giá Nấm da',
    category: 'Nấm da',
    status: 'active',
    questions: [],
  },
];

// Triage level colors
const TRIAGE_COLORS = {
  light: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Nhẹ' },
  moderate: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Vừa' },
  severe: { bg: 'bg-red-100', text: 'text-red-700', label: 'Nặng' },
};

const STATUS_COLORS = {
  active: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Hoạt động' },
  draft: { bg: 'bg-slate-100', text: 'text-slate-700', label: 'Nháp' },
};

export default function QuestionnaireAdmin() {
  const [questionnaires, setQuestionnaires] = useState<Questionnaire[]>(DUMMY_QUESTIONNAIRES);
  const [selectedId, setSelectedId] = useState<string>('1');
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set(['q1']));

  const selected = questionnaires.find((q) => q.id === selectedId);

  const toggleQuestion = (questionId: string) => {
    const newExpanded = new Set(expandedQuestions);
    if (newExpanded.has(questionId)) {
      newExpanded.delete(questionId);
    } else {
      newExpanded.add(questionId);
    }
    setExpandedQuestions(newExpanded);
  };

  const toggleStatus = () => {
    setQuestionnaires(
      questionnaires.map((q) =>
        q.id === selectedId ? { ...q, status: q.status === 'active' ? 'draft' : 'active' } : q
      )
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-emerald-50 to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">Quản lý Bộ Câu Hỏi Sơ Cứu</h1>
          <p className="text-muted-foreground">Quản lý và tổ chức các bộ câu hỏi đánh giá y tế</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Questionnaire List */}
          <div className="lg:col-span-1">
            <div className="space-y-4">
              {/* Create New Button */}
              <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg hover:shadow-xl transition-shadow rounded-lg font-semibold h-11">
                <PlusCircle className="mr-2 h-5 w-5" />
                Tạo Bộ Câu Hỏi Mới
              </Button>

              {/* Questionnaire List */}
              <Card className="p-0 border-0 shadow-md bg-card/95 backdrop-blur-sm overflow-hidden">
                <div className="divide-y divide-border">
                  {questionnaires.map((q) => (
                    <button
                      key={q.id}
                      onClick={() => setSelectedId(q.id)}
                      className={`w-full text-left p-4 transition-all duration-200 hover:bg-secondary/50 ${
                        selectedId === q.id ? 'bg-secondary border-l-4 border-primary' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-foreground truncate text-sm">
                            {q.name}
                          </h3>
                          <p className="text-xs text-muted-foreground mt-1">{q.category}</p>
                        </div>
                        <Badge
                          variant="secondary"
                          className={`${STATUS_COLORS[q.status].bg} ${STATUS_COLORS[q.status].text} text-xs font-medium shrink-0`}
                        >
                          {STATUS_COLORS[q.status].label}
                        </Badge>
                      </div>
                    </button>
                  ))}
                </div>
              </Card>
            </div>
          </div>

          {/* Right Panel - Questionnaire Details */}
          {selected && (
            <div className="lg:col-span-2">
              <Card className="border-0 shadow-lg bg-card/95 backdrop-blur-sm p-6 sticky top-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-6 pb-6 border-b border-border">
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold text-foreground mb-2">{selected.name}</h2>
                    <p className="text-sm text-muted-foreground">Danh mục: {selected.category}</p>
                  </div>
                  <Button
                    onClick={toggleStatus}
                    variant={selected.status === 'active' ? 'default' : 'outline'}
                    className={`${
                      selected.status === 'active'
                        ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                        : 'border-border'
                    }`}
                  >
                    {selected.status === 'active' ? '✓ Hoạt động' : '○ Nháp'}
                  </Button>
                </div>

                {/* Questions Section */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-primary" />
                    Danh Sách Câu Hỏi ({selected.questions.length})
                  </h3>

                  {selected.questions.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 px-4 bg-secondary/30 rounded-lg border border-border">
                      <AlertCircle className="h-12 w-12 text-muted-foreground mb-2" />
                      <p className="text-muted-foreground text-center">
                        Chưa có câu hỏi nào. Hãy thêm câu hỏi đầu tiên.
                      </p>
                      <Button className="mt-4 bg-primary hover:bg-primary/90 text-primary-foreground">
                        <Plus className="mr-2 h-4 w-4" />
                        Thêm Câu Hỏi
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {selected.questions.map((question) => (
                        <div key={question.id} className="border border-border rounded-lg overflow-hidden bg-white/50 dark:bg-slate-800/30 hover:border-primary/50 transition-colors">
                          {/* Question Header */}
                          <button
                            onClick={() => toggleQuestion(question.id)}
                            className="w-full p-4 flex items-center gap-3 hover:bg-secondary/20 transition-colors"
                          >
                            <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab active:cursor-grabbing" />
                            <ChevronDown
                              className={`h-4 w-4 text-muted-foreground transition-transform ${
                                expandedQuestions.has(question.id) ? 'rotate-180' : ''
                              }`}
                            />
                            <div className="flex-1 text-left">
                              <p className="font-medium text-foreground">
                                Q{question.order}: {question.title}
                              </p>
                            </div>
                            <div className="flex gap-2 opacity-0 hover:opacity-100 transition-opacity">
                              <button className="p-1 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded transition-colors">
                                <Edit2 className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                              </button>
                              <button className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors">
                                <Trash2 className="h-4 w-4 text-red-600 dark:text-red-400" />
                              </button>
                            </div>
                          </button>

                          {/* Answers Section */}
                          {expandedQuestions.has(question.id) && (
                            <div className="border-t border-border bg-secondary/20 p-4 space-y-3">
                              <div className="flex items-center justify-between mb-3">
                                <h4 className="text-sm font-semibold text-foreground">
                                  Đáp Án ({question.answers.length})
                                </h4>
                                <Button size="sm" variant="outline" className="h-8 text-xs">
                                  <Plus className="mr-1 h-3 w-3" />
                                  Thêm Đáp Án
                                </Button>
                              </div>

                              <div className="space-y-2">
                                {question.answers.map((answer) => (
                                  <div
                                    key={answer.id}
                                    className="flex items-center gap-3 p-3 bg-white dark:bg-slate-800 rounded-lg border border-border hover:border-primary/50 transition-colors group"
                                  >
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm text-foreground truncate">{answer.text}</p>
                                    </div>
                                    <Badge
                                      className={`${TRIAGE_COLORS[answer.triageLevel].bg} ${TRIAGE_COLORS[answer.triageLevel].text} text-xs font-semibold shrink-0`}
                                    >
                                      {TRIAGE_COLORS[answer.triageLevel].label}
                                    </Badge>
                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                      <button className="p-1 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded transition-colors">
                                        <Edit2 className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                                      </button>
                                      <button className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors">
                                        <Trash2 className="h-3 w-3 text-red-600 dark:text-red-400" />
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}

                      {/* Add Question Button */}
                      <Button
                        variant="outline"
                        className="w-full border-dashed border-primary/50 text-primary hover:bg-primary/5 hover:border-primary"
                      >
                        <PlusCircle className="mr-2 h-4 w-4" />
                        Thêm Câu Hỏi Mới
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

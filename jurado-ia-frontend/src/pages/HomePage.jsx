import React, { useState } from 'react';
import axios from 'axios';
import '../App.css'; // Usamos o mesmo CSS

// --- COMPONENTES INTERNOS DA PÁGINA ---

function ResultsDisplay({ result }) {
  if (!result) return null;
  if (result.erro) { return <div className="results-container error-message">Erro na análise: {result.erro}</div>; }
  return (
    <div className="results-card">
      <h2>Resultado da Análise 📊</h2>
      <div className="score">
        <strong>Pontuação:</strong> {result.pontuacao} / {result.pontuacao_maxima || 100}
      </div>
      <p><strong>Feedback:</strong> {result.feedback}</p>
      <div className="details">
        <div className="fortes">
          <h3>Pontos Fortes:</h3>
          <ul>{result.pontos_fortes?.map((point, index) => <li key={index}>{point}</li>)}</ul>
        </div>
        <div className="melhoria">
          <h3>Pontos de Melhoria:</h3>
          <ul>{result.pontos_melhoria?.map((point, index) => <li key={index}>{point}</li>)}</ul>
        </div>
      </div>
      <p className="verdict"><strong>Resumo:</strong> {result.veredicto}</p>
    </div>
  );
}

function CompetitionResultsDisplay({ result }) {
  if (!result) return null;
  const { analises_individuais = [], sintese_final = {} } = result;
  return (
    <div className="results-container">
      <div className="results-card synthesis-card">
        <h2>Síntese da Competição 🏆</h2>
        <div className="score"><strong>Pontuação Final (Média):</strong> {sintese_final.pontuacao_final?.toFixed(2) || 'N/A'}</div>
        <p><strong>Veredicto Geral:</strong> {sintese_final.veredicto_geral}</p>
        <p><strong>Recomendação:</strong> {sintese_final.recomendacao}</p>
      </div>
      <h2>Ranking Individual</h2>
      {analises_individuais.map((item, index) => (
        <div key={index} className="results-card-small">
          <h3>{item.posicao || index + 1}. {item.content_name} ({item.pontuacao} / {item.pontuacao_maxima || 100}) {item.medalha}</h3>
          <p><strong>Veredicto:</strong> {item.veredicto}</p>
        </div>
      ))}
    </div>
  );
}

function SingleAnalysis() {
  const [file, setFile] = useState(null);
  const [criteria, setCriteria] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [fileName, setFileName] = useState('');
  const handleFileChange = (e) => { const selectedFile = e.target.files[0]; if (selectedFile) { setFile(selectedFile); setFileName(selectedFile.name); setResult(null); setError(''); } };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) { setError('Por favor, selecione um arquivo.'); return; }
    setIsLoading(true); setError(''); setResult(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('criteria', criteria || 'Análise geral de qualidade');
    let endpoint = '';
    const fileType = file.type;
    if (fileType.startsWith('image/')) { endpoint = '/analyze/image'; }
    else if (fileType.startsWith('audio/')) { endpoint = '/analyze/audio'; }
    else if (fileType.startsWith('video/')) { endpoint = '/analyze/video'; }
    else if (fileType === 'application/pdf') { endpoint = '/analyze/document'; }
    else { setError(`Tipo de arquivo "${fileType}" não suportado.`); setIsLoading(false); return; }
    const backendUrl = `http://localhost:8000${endpoint}`;
    try {
      const response = await axios.post(backendUrl, formData);
      if (response.data.success) { setResult(response.data.data); }
      else { setError(response.data.error || 'Ocorreu um erro na análise.'); }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erro de conexão com o servidor. O back-end está rodando?';
      setError(errorMsg);
    } finally { setIsLoading(false); }
  };
  return (
    <div className="tab-content">
      <div className="tab-header">
        <i className="fas fa-user-edit"></i>
        <h3>Análise Individual</h3>
      </div>
      <p>Faça o upload de um arquivo para uma análise detalhada.</p>
      <form onSubmit={handleSubmit}>
        <label htmlFor="single-file-upload" className="upload-area">
          <i className="fas fa-cloud-upload-alt"></i><p>{fileName || 'Clique para fazer o upload ou arraste e solte'}</p><span>Suporta: Imagens, Áudio, Vídeo e PDF</span>
        </label>
        <input id="single-file-upload" type="file" onChange={handleFileChange} accept="image/*,audio/*,video/*,.pdf" />
        <div className="criteria-input">
          <label htmlFor="criteria-single">Critérios de Avaliação</label>
          <input id="criteria-single" type="text" value={criteria} onChange={(e) => setCriteria(e.target.value)} placeholder="Análise geral de qualidade" />
        </div>
        <button type="submit" className="main-button" disabled={isLoading || !file}>{isLoading ? 'Analisando...' : 'Analisar Arquivo'}</button>
      </form>
      {error && <p className="error-message">{error}</p>}
      {isLoading && (<div className="loading-overlay"><div className="loader"></div><p>Analisando com Gemini...</p><span>Isso pode levar alguns segundos.</span></div>)}
      <ResultsDisplay result={result} />
    </div>
  );
}

function CompetitionAnalysis() {
  const [files, setFiles] = useState([]);
  const [criteria, setCriteria] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const handleFileChange = (e) => { setFiles([...e.target.files]); setResult(null); setError(''); };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (files.length === 0) { setError('Por favor, selecione pelo menos um arquivo.'); return; }
    setIsLoading(true); setError(''); setResult(null);
    const formData = new FormData();
    files.forEach(file => { formData.append('files', file); });
    formData.append('criteria', criteria || 'Avaliação comparativa de qualidade');
    const backendUrl = `http://localhost:8000/analyze/multiple`;
    try {
      const response = await axios.post(backendUrl, formData);
      if (response.data.success) {
        const sortedData = response.data.data;
        sortedData.analises_individuais.sort((a, b) => (b.pontuacao || 0) - (a.pontuacao || 0));
        sortedData.analises_individuais.forEach((item, index) => {
          item.posicao = index + 1;
          if (index === 0) item.medalha = '🥇';
          if (index === 1) item.medalha = '🥈';
          if (index === 2) item.medalha = '🥉';
        });
        setResult(sortedData);
      } else { setError(response.data.error || 'Ocorreu um erro na análise.'); }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erro de conexão com o servidor. O back-end está rodando?';
      setError(errorMsg);
    } finally { setIsLoading(false); }
  };
  return (
    <div className="tab-content">
      <div className="tab-header">
        <i className="fas fa-users"></i>
        <h3>Modo Competição</h3>
      </div>
      <p>Faça o upload de múltiplos arquivos para compará-los e obter uma síntese final.</p>
      <form onSubmit={handleSubmit}>
        <label htmlFor="multi-file-upload" className="upload-area">
          <i className="fas fa-cloud-upload-alt"></i><p>{files.length > 0 ? `${files.length} arquivos selecionados` : 'Clique para fazer o upload ou arraste e solte'}</p><span>Suporta: Imagens, Áudio, Vídeo e PDF</span>
        </label>
        <input id="multi-file-upload" type="file" multiple onChange={handleFileChange} accept="image/*,audio/*,video/*,.pdf" />
        <div className="file-list">{files.map((file, index) => (<span key={index} className="file-tag">{file.name}</span>))}</div>
        <div className="criteria-input">
          <label htmlFor="criteria-competition">Critérios da Competição</label>
          <input id="criteria-competition" type="text" value={criteria} onChange={(e) => setCriteria(e.target.value)} placeholder="Avaliação comparativa de qualidade" />
        </div>
        <button type="submit" className="main-button" disabled={isLoading || files.length === 0}>{isLoading ? 'Analisando...' : `Analisar ${files.length} Itens`}</button>
      </form>
      {error && <p className="error-message">{error}</p>}
      {isLoading && (<div className="loading-overlay"><div className="loader"></div><p>Analisando com Gemini...</p><span>Isso pode levar alguns segundos.</span></div>)}
      <CompetitionResultsDisplay result={result} />
    </div>
  );
}


// --- COMPONENTE PRINCIPAL DA PÁGINA DE INÍCIO ---
function HomePage() {
  const [mode, setMode] = useState('single');
  
  return (
    <>
      <section className="hero-section" id="inicio">
        <div className="container">
          <h1>Análise Jurídica com Inteligência Artificial</h1>
          <p className="subtitle">Obtenha feedback detalhado e pontuações profissionais para seus documentos e arquivos com a nossa poderosa IA.</p>
          
          {/* ÍCONES ADICIONADOS PARA PREENCHER O ESPAÇO */}
          <div className="hero-icons">
            <div className="hero-icon-item">
              <i className="fas fa-file-pdf"></i>
              <span>PDFs e Docs</span>
            </div>
            <div className="hero-icon-item">
              <i className="fas fa-image"></i>
              <span>Imagens</span>
            </div>
            <div className="hero-icon-item">
              <i className="fas fa-video"></i>
              <span>Vídeos</span>
            </div>
             <div className="hero-icon-item">
              <i className="fas fa-music"></i>
              <span>Áudios</span>
            </div>
          </div>
        </div>
      </section>

      <section className="app-section">
        <div className="container">
          <div className="mode-description-cards">
            <div className="description-card">
              <h4>Análise Individual</h4>
              <p>Faça o upload de um único arquivo para receber uma pontuação detalhada e um feedback completo da IA.</p>
            </div>
            <div className="description-card">
              <h4>Modo Competição</h4>
              <p>Envie múltiplos arquivos e receba um ranking comparativo com uma análise final.</p>
            </div>
          </div>
          <div className="main-content-card">
            <nav className="nav-tabs">
              <button onClick={() => setMode('single')} className={mode === 'single' ? 'active' : ''}>Análise Individual</button>
              <button onClick={() => setMode('competition')} className={mode === 'competition' ? 'active' : ''}>Modo Competição</button>
            </nav>
            {mode === 'single' ? <SingleAnalysis /> : <CompetitionAnalysis />}
          </div>
        </div>
      </section>
    </>
  );
}

export default HomePage;
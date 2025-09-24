import React from 'react';
import { Link } from 'react-router-dom';
// É uma boa prática importar o CSS principal para manter a consistência de fontes e cores
import '../App.css'; 

function AboutPage() {
  return (
    <div className="container about-page">
      <h2>Democratizando a Análise de Elite</h2>
      <p className="about-subtitle">
        Nossa missão no Jurado IA é fornecer feedback instantâneo, objetivo e com a profundidade de um especialista, 
        transformando a maneira como criadores, profissionais e empresas avaliam e aprimoram seu conteúdo.
      </p>

      <div className="about-content">
        <h3>Para Quem é o Jurado IA?</h3>
        <div className="features-grid">
          <div className="feature-card">
            <i className="fas fa-paint-brush"></i>
            <h4>Criadores de Conteúdo</h4>
            <p>Receba uma segunda opinião imparcial sobre seus vídeos, podcasts, designs e textos.</p>
          </div>
          <div className="feature-card">
            <i className="fas fa-briefcase"></i>
            <h4>Profissionais de Marketing</h4>
            <p>Compare diferentes versões de campanhas e tome decisões baseadas em dados.</p>
          </div>
          <div className="feature-card">
            <i className="fas fa-graduation-cap"></i>
            <h4>Estudantes e Acadêmicos</h4>
            <p>Aprimore a qualidade de seus trabalhos, teses e apresentações com um feedback estruturado.</p>
          </div>
          <div className="feature-card">
            <i className="fas fa-rocket"></i>
            <h4>Startups e Empreendedores</h4>
            <p>Refine seu pitch deck. Nossa IA analisa a clareza, coesão e design da sua apresentação.</p>
          </div>
        </div>
      </div>

      <Link to="/" className="cta-button">
        Voltar para a Análise
      </Link>
    </div>
  );
}

export default AboutPage;